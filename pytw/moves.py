from __future__ import annotations

import traceback
import typing
from typing import Callable

from pytw.config import GameConfig
from pytw.planet import CommodityType
from pytw.planet import Galaxy
from pytw.planet import Player
from pytw.planet import Port
from pytw.planet import Sector
from pytw.planet import Ship
from pytw.planet import TradingCommodity
from pytw.util import methods_to_json

if typing.TYPE_CHECKING:
    from pytw.server import Server


class GameConfigPublic:
    def __init__(self, config: GameConfig, sectors_count: int):
        self.id = config.id
        self.name = config.name
        self.diameter = config.diameter
        self.sectors_count = sectors_count


class PlayerPublic:
    def __init__(self, player: Player):
        self.id = player.id
        self.name = player.name
        self.ship = ShipPublic(player.ship, player.sector)
        self.credits = player.credits
        self.sector = SectorPublic(player.sector)
        self.port = None if not player.port else PortPublic(player.port)


class TraderPublic:
    def __init__(self, player: Player):
        self.id = player.id
        self.name = player.name


class TraderShipPublic:
    def __init__(self, ship: Ship):
        self.id = ship.id
        self.name = ship.name
        self.type = ship.ship_type
        self.trader = TraderPublic(ship.player)


class ShipPublic:
    def __init__(self, ship: Ship, sector: Sector):
        self.id = ship.id
        self.name = ship.name
        self.type = ship.ship_type
        self.holds_capacity = ship.holds_capacity
        self.holds = {t.name: val for t, val in ship.holds.items()}
        self.sector = SectorPublic(sector)


class TradingCommodityPublic:
    def __init__(self, commodity: TradingCommodity):
        self.amount = commodity.amount
        self.capacity = commodity.capacity
        self.buying = commodity.buying
        self.type = commodity.type.name
        self.price = commodity.price


class PortPublic:
    def __init__(self, port: Port):
        self.name = port.name
        self.sector_id = port.sector_id
        self.commodities = [TradingCommodityPublic(c) for c in port.commodities]


class SectorPublic:
    def __init__(self, sector: Sector):
        self.id = sector.id
        self.coords = sector.coords
        self.warps = sector.warps
        if sector.port:
            self.port = PortPublic(sector.port)
            for c in self.port.commodities:
                c.amount = None
                c.capacity = None
                c.price = None
        else:
            self.port = None
        self.ships = [TraderShipPublic(ship) for ship in sector.ships]


@methods_to_json()
class ServerEvents:
    def __init__(self, target: Callable[[str], None]):
        self.target = target

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

    def __init__(self, server: Server, player: Player, galaxy: Galaxy,
                 events: ServerEvents):
        super().__init__()
        self.galaxy = galaxy
        self.player = player
        self.events = events
        self.server = server

    async def move_trader(self, sector_id: int):
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
                error="Target sector not adjacent to ship")
            return

        try:
            ship_sector.exit_ship(ship)
            target.enter_ship(ship)
            ship.move_sector(target.id)
            self.player.visit_sector(target.id)
            target_public = SectorPublic(target)
            await self.events.on_new_sector(sector=target_public)

            ship_as_trader = TraderShipPublic(ship)
            for ship in (s for s in ship_sector.ships if s.player_id != self.player.id):
                if ship.player_id in self.server.sessions:
                    await self.server.sessions[ship.player_id].on_ship_exit_sector(
                        sector=SectorPublic(ship_sector), ship=ship_as_trader)

            await self.broadcast_ship_enter_sector(ship_as_trader, target_public)
        except Exception:
            traceback.print_exc()

    async def broadcast_player_enter_sector(self, player: Player):
        await self.broadcast_ship_enter_sector(TraderShipPublic(player.ship),
                                               SectorPublic(player.sector))

    async def broadcast_ship_enter_sector(self, ship_as_trader: TraderShipPublic,
                                          target: SectorPublic):
        for ship in (s for s in target.ships if s.trader.id != self.player.id):
            if ship.trader.id in self.server.sessions:
                await self.server.sessions[ship.trader.id].on_ship_enter_sector(
                    sector=target,
                    ship=ship_as_trader)

    async def enter_port(self, port_id: int):
        port: Port = self.galaxy.sectors[port_id].port
        self.player.port = port
        await self.server.sessions[self.player.id].on_port_enter(port=PortPublic(port),
                                                                 player=PlayerPublic(
                                                                     self.player))

    async def exit_port(self, port_id: int):
        port: Port = self.galaxy.sectors[port_id].port
        self.player.port = None
        await self.server.sessions[self.player.id].on_port_exit(port=PortPublic(port),
                                                                player=PlayerPublic(self.player))

    async def sell_to_port(self, id: int, commodity: CommodityType, amount: int):
        ship = self.galaxy.ships[self.player.ship_id]  # type: Ship
        port = self.galaxy.sectors[ship.sector_id].port  # type: Port

        try:
            amount = int(amount)
        except ValueError:
            await self.events.on_invalid_action(error="Not a valid number")
            return

        trading = port.commodity(commodity)
        if not trading.buying:
            await self.events.on_invalid_action(
                error="This port is not buying that commodity")
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

        await self.events.on_port_sell(id=id, player=PlayerPublic(self.player))

    async def buy_from_port(self, id: int, commodity: CommodityType, amount: int):
        ship = self.galaxy.ships[self.player.ship_id]  # type: Ship
        port = self.galaxy.sectors[ship.sector_id].port  # type: Port

        try:
            amount = int(amount)
        except ValueError:
            await self.events.on_invalid_action(error="Not a valid number")
            return

        trading = port.commodity(commodity)
        if trading.buying:
            await self.events.on_invalid_action(
                error="This port is not selling that commodity")
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

        await self.events.on_port_buy(id=id, player=PlayerPublic(self.player))
