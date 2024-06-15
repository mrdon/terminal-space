from __future__ import annotations

import asyncio
import traceback
import typing
from typing import Callable

from pydantic import BaseModel

from tspace.common.background import schedule_background_task
from tspace.server.config import GameConfig
from tspace.server.models import CommodityType, ShipType
from tspace.server.models import Planet
from tspace.server.models import Player
from tspace.server.models import Port
from tspace.server.models import Sector
from tspace.server.models import Ship
from tspace.server.models import TradingCommodity

if typing.TYPE_CHECKING:
    from tspace.server.server import Server
    from tspace.server.models import Galaxy


class GameConfigPublic(BaseModel):
    id: int
    name: str
    diameter: int
    sectors_count: int

    @staticmethod
    def from_inner(config: GameConfig, sectors_count: int) -> GameConfigPublic:
        return GameConfigPublic(
            id=config.id,
            name=config.name,
            diameter=config.diameter,
            sectors_count=sectors_count,
        )


class PlayerPublic(BaseModel):
    id: int
    name: str
    ship: ShipPublic
    credits: int
    sector: SectorPublic
    port: PortPublic | None

    @staticmethod
    def from_inner(player: Player) -> PlayerPublic:
        return PlayerPublic(
            id=player.id,
            name=player.name,
            ship=ShipPublic.from_inner(player.ship, player.sector),
            credits=player.credits,
            sector=SectorPublic.from_inner(player.sector),
            port=None if not player.port else PortPublic.from_inner(player.port),
        )


class TraderPublic(BaseModel):
    id: int
    name: str

    @staticmethod
    def from_inner(player: Player) -> TraderPublic:
        return TraderPublic(
            id=player.id,
            name=player.name,
        )


class TraderShipPublic(BaseModel):
    id: int
    name: str
    type: ShipType
    trader: TraderPublic

    @staticmethod
    def from_inner(ship: Ship) -> TraderShipPublic:
        return TraderShipPublic(
            id=ship.id,
            name=ship.name,
            type=ship.ship_type,
            trader=TraderPublic.from_inner(ship.player)
        )


class ShipPublic(BaseModel):
    id: int
    name: str
    holds_capacity: int
    holds: dict[CommodityType, int]
    sector: SectorPublic
    type: str

    @staticmethod
    def from_inner(ship: Ship, sector: Sector) -> ShipPublic:
        return ShipPublic(
            id=ship.id,
            name=ship.name,
            holds_capacity=ship.holds_capacity,
            holds={t: val for t, val in ship.holds.items()},
            sector=SectorPublic.from_inner(sector),
            type=ship.ship_type.name,
        )


class TradingCommodityPublic(BaseModel):
    amount: int | None
    capacity: int | None
    buying: bool
    type: str
    price: float | None

    @staticmethod
    def from_inner(commodity: TradingCommodity) -> TradingCommodityPublic:
        return TradingCommodityPublic(
            amount=commodity.amount,
            capacity=commodity.capacity,
            buying=commodity.buying,
            type=commodity.type.name,
            price=commodity.price,
        )


class PortPublic(BaseModel):
    id: int
    name: str
    sector_id: int
    commodities: list[TradingCommodityPublic]

    @staticmethod
    def from_inner(port: Port) -> PortPublic:
        return PortPublic(
            id=port.id,
            name=port.name,
            sector_id=port.sector_id,
            commodities=[TradingCommodityPublic.from_inner(c) for c in port.commodities]
        )


class SectorPublic(BaseModel):
    id: int
    coords: tuple[int, int]
    warps: list[int]
    ports: list[PortPublic]
    ships: list[TraderShipPublic]
    planets: list[PlanetPublic]

    @staticmethod
    def from_inner(sector: Sector) -> SectorPublic:

        ports = [PortPublic.from_inner(port) for port in sector.ports]
        for port in ports:
            for c in port.commodities:
                c.amount = None
                c.capacity = None
                c.price = None

        return SectorPublic(
            id=sector.id,
            coords=sector.coords,
            warps=sector.warps,
            ports=ports,
            ships=[TraderShipPublic.from_inner(ship) for ship in sector.ships],
            planets=[PlanetPublic.from_inner(planet) for planet in sector.planets],
        )


class PlanetPublic(BaseModel):
    id: int
    name: str
    owner: TraderPublic | None
    planet_type: str
    fuel_ore: int
    organics: int
    equipment: int

    @staticmethod
    def from_inner(planet: Planet) -> PlanetPublic:
        return PlanetPublic(
            id=planet.id,
            name=planet.name,
            owner=TraderPublic.from_inner(planet.owner) if planet.owner else None,
            planet_type=planet.planet_type,
            fuel_ore=planet.fuel_ore,
            organics=planet.organics,
            equipment=planet.equipment,
        )


class Reply(BaseModel):
    parent_id: str
    args: list[typing.Any]
    type: str = "reply"


# @methods_to_json()
class ServerEvents:
    async def on_game_enter(self, player: PlayerPublic, config: GameConfigPublic):
        pass

    async def on_new_sector(self, sector: SectorPublic):
        pass

    async def on_ship_enter_sector(self, sector: SectorPublic, ship: TraderShipPublic):
        pass

    async def on_ship_exit_sector(self, sector: SectorPublic, ship: TraderShipPublic):
        pass

    async def on_invalid_action(self, error: str):
        pass

    async def on_port_enter(self, port: PortPublic, player: PlayerPublic):
        pass

    async def on_port_exit(self, port: PortPublic, player: PlayerPublic):
        pass

    async def on_port_buy(self, id: int, player: PlayerPublic):
        pass

    async def on_port_sell(self, id: int, player: PlayerPublic):
        pass


class ShipMoves:
    def __init__(
        self, server: Server, player: Player, galaxy: Galaxy, events: ServerEvents
    ):
        super().__init__()
        self.galaxy = galaxy
        self.player = player
        self.events = events
        self.server = server

    async def move_trader(self, sector_id: int, **kwargs) -> SectorPublic | None:
        if sector_id not in self.galaxy.sectors:
            await self.events.on_invalid_action(error="Not a valid sector number")
            return

        target = self.galaxy.sectors[sector_id]
        ship = self.galaxy.ships[self.player.ship_id]
        ship_sector = self.galaxy.sectors[ship.sector_id]

        if ship.player_id != self.player.id:
            await self.events.on_invalid_action(error="Ship not occupied by player")
            return

        if not ship_sector.can_warp(target.id):
            await self.events.on_invalid_action(
                error="Target sector not adjacent to ship"
            )
            return

        try:
            ship_sector.exit_ship(ship)
            target.enter_ship(ship)
            ship.move_sector(target.id)
            self.player.visit_sector(target.id)
            target_public = SectorPublic.from_inner(target)

            async def do_after():
                ship_as_trader = TraderShipPublic.from_inner(ship)
                for ship_other in (s for s in ship_sector.ships if s.player_id != self.player.id):
                    if ship_other.player_id in self.server.sessions:
                        await self.server.sessions[ship_other.player_id].on_ship_exit_sector(
                            sector=SectorPublic.from_inner(ship_sector), ship=ship_as_trader
                        )

                await self._broadcast_ship_enter_sector(ship_as_trader, target_public)

            schedule_background_task(do_after())
            return target_public
        except Exception:
            traceback.print_exc()

    async def _broadcast_player_enter_sector(self, player: Player):
        await self._broadcast_ship_enter_sector(
            TraderShipPublic.from_inner(player.ship), SectorPublic.from_inner(player.sector)
        )

    async def _broadcast_ship_enter_sector(
        self, ship_as_trader: TraderShipPublic, target: SectorPublic
    ):
        for ship in (s for s in target.ships if s.trader.id != self.player.id):
            if ship.trader.id in self.server.sessions:
                await self.server.sessions[ship.trader.id].on_ship_enter_sector(
                    sector=target, ship=ship_as_trader
                )

    async def enter_port(self, port_id: int, **kwargs) -> None:
        port: Port = self.galaxy.ports[port_id]
        self.player.port = port
        await self.server.sessions[self.player.id].on_port_enter(
            port=PortPublic.from_inner(port), player=PlayerPublic.from_inner(self.player)
        )

    async def exit_port(self, port_id: int):
        port: Port = self.galaxy.ports[port_id]
        self.player.port = None
        await self.server.sessions[self.player.id].on_port_exit(
            port=PortPublic.from_inner(port), player=PlayerPublic.from_inner(self.player)
        )

    async def sell_to_port(
        self, port_id: int, commodity: CommodityType, amount: int
    ) -> tuple[PlayerPublic, PortPublic] | None:
        ship = self.galaxy.ships[self.player.ship_id]
        port = self.galaxy.ports[port_id]

        try:
            amount = int(amount)
        except ValueError:
            await self.events.on_invalid_action(error="Not a valid number")
            return

        trading = port.commodity(commodity)
        if not trading.buying:
            await self.events.on_invalid_action(
                error="This port is not buying that commodity"
            )
            return

        if trading.amount < amount:
            await self.events.on_invalid_action(error="Not that many available")
            return

        if ship.holds.get(commodity, 0) < amount:
            await self.events.on_invalid_action(error="Not enough goods in your holds")
            return

        cost = int(trading.price * amount)
        self.player.credits += cost
        trading.amount -= amount
        ship.remove_from_holds(commodity, amount)

        return PlayerPublic.from_inner(self.player), PortPublic.from_inner(port)

    async def buy_from_port(
        self,
        port_id: int,
        commodity: CommodityType,
        amount: int,
    ) -> tuple[PlayerPublic, PortPublic] | None:
        ship = self.galaxy.ships[self.player.ship_id]
        port = self.galaxy.ports[port_id]

        try:
            amount = int(amount)
        except ValueError:
            await self.events.on_invalid_action(error="Not a valid number")
            return

        trading = port.commodity(commodity)
        if trading.buying:
            await self.events.on_invalid_action(
                error="This port is not selling that commodity"
            )
            return

        if trading.amount < amount:
            await self.events.on_invalid_action(error="Not that many available")
            return

        cost = int(trading.price * amount)
        if cost > self.player.credits:
            await self.events.on_invalid_action(error="Not enough credits available")
            return

        if ship.holds_free < amount:
            await self.events.on_invalid_action(error="Not enough holds available")
            return

        self.player.credits -= cost
        trading.amount -= amount
        ship.add_to_holds(commodity, amount)

        return PlayerPublic.from_inner(self.player), PortPublic.from_inner(port)
