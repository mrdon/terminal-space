import traceback
import typing

from tspace.common.background import schedule_background_task
from tspace.common.events import ServerEvents
from tspace.common.models import (
    PlayerPublic,
    SectorPublic,
    TraderShipPublic,
    PortPublic,
)
from tspace.common.actions import SectorActions, PortActions
from tspace.server.galaxy import Galaxy
from tspace.server.models import CommodityType
from tspace.server.models import Player
from tspace.server.models import Port


# @methods_to_json()
class ShipMoves(SectorActions, PortActions):
    def __init__(
        self,
        sessions: typing.Callable[[], dict[int, ServerEvents]],
        player: Player,
        galaxy: Galaxy,
        events: ServerEvents,
    ):
        super().__init__()
        self.galaxy = galaxy
        self.player = player
        self.events = events
        self.sessions = sessions

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
            target_public = target.to_public()

            async def do_after():
                ship_as_trader = ship.to_trader()
                for ship_other in (
                    s for s in ship_sector.ships if s.player_id != self.player.id
                ):
                    if ship_other.player_id in self.sessions():
                        await self.sessions()[ship_other.player_id].on_ship_exit_sector(
                            sector=ship_sector.to_public(), ship=ship_as_trader
                        )

                await self._broadcast_ship_enter_sector(ship_as_trader, target_public)

            schedule_background_task(do_after())
            return target_public
        except Exception:
            traceback.print_exc()

    async def _broadcast_player_enter_sector(self, player: Player):
        await self._broadcast_ship_enter_sector(
            player.ship.to_trader(), player.sector.to_public()
        )

    async def _broadcast_ship_enter_sector(
        self, ship_as_trader: TraderShipPublic, target: SectorPublic
    ):
        for ship in (s for s in target.ships if s.trader.id != self.player.id):
            if ship.trader.id in self.sessions():
                await self.sessions()[ship.trader.id].on_ship_enter_sector(
                    sector=target, ship=ship_as_trader
                )

    async def enter_port(
        self, port_id: int, **kwargs
    ) -> tuple[PlayerPublic, PortPublic]:
        port: Port = self.galaxy.ports[port_id]
        self.player.port = port
        return self.player.to_public(), port.to_public()

    async def exit_port(self, port_id: int) -> PlayerPublic:
        self.player.port = None
        return self.player.to_public()

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

        return self.player.to_public(), port.to_public()

    async def buy_from_port(
        self,
        port_id: int,
        commodity: str,
        amount: int,
    ) -> tuple[PlayerPublic, PortPublic] | None:
        commodity = CommodityType[commodity]
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

        return self.player.to_public(), port.to_public()
