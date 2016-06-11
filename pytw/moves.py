from typing import Callable

from pytw.planet import Galaxy, Player, Sector, Ship, Port, TradingCommodity, CommodityType
from pytw.util import methods_to_json


class PlayerPublic:
    def __init__(self, player: Player):
        self.id = player.id
        self.name = player.name
        self.ship = ShipPublic(player.ship, player.sector)
        self.credits = player.credits
        self.visited = list(player.visited_sectors.keys())


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
        self.port = None if not sector.port else PortPublic(sector.port)
        self.ships = [TraderShipPublic(ship) for ship in sector.ships]


@methods_to_json()
class ServerEvents:
    def __init__(self, target: Callable[[str], None]):
        self.target = target

    def on_game_enter(self, player: PlayerPublic):
        pass

    def on_new_sector(self, sector: SectorPublic):
        pass

    def on_ship_enter_sector(self, sector: SectorPublic, ship: TraderShipPublic):
        pass

    def on_ship_exit_sector(self, sector: SectorPublic, ship: TraderShipPublic):
        pass

    def on_invalid_action(self, error: str):
        pass

    def on_port_buy(self, id: int, player: PlayerPublic):
        pass

    def on_port_sell(self, id: int, player: PlayerPublic):
        pass


class ShipMoves:

    def __init__(self, server, player, galaxy: Galaxy, events: ServerEvents):
        super().__init__()
        self.galaxy = galaxy
        self.player = player
        self.events = events
        self.server = server

        self.events.on_game_enter(player=PlayerPublic(player))

    def move_trader(self, sector_id: int):
        if sector_id not in self.galaxy.sectors:
            self.events.on_invalid_action(error="Not a valid sector number")
            return

        target = self.galaxy.sectors[sector_id]
        ship = self.galaxy.ships[self.player.ship_id]
        ship_sector = self.galaxy.sectors[ship.sector_id]

        if ship.player_id != self.player.id:
            self.events.on_invalid_action(error="Ship not occupied by player")
            return

        if not ship_sector.can_warp(target.id):
            self.events.on_invalid_action(error="Target sector not adjacent to ship")
            return

        ship_sector.exit_ship(ship)
        target.enter_ship(ship)
        ship.move_sector(target.id)
        self.player.visit_sector(target.id)
        target_public = SectorPublic(target)
        self.events.on_new_sector(sector=target_public)

        ship_as_trader = TraderShipPublic(ship)
        for ship in (s for s in ship_sector.ships if s.player_id != self.player.id):
            if ship.player_id in self.server.sessions:
                self.server.sessions[ship.player_id].on_ship_exit_sector(sector=SectorPublic(ship_sector), ship=ship_as_trader)

        self.broadcast_ship_enter_sector(ship_as_trader, target_public)

    def broadcast_player_enter_sector(self, player: Player):
        self.broadcast_ship_enter_sector(TraderShipPublic(player.ship), SectorPublic(player.sector))

    def broadcast_ship_enter_sector(self, ship_as_trader: TraderShipPublic, target: SectorPublic):
        for ship in (s for s in target.ships if s.trader.id != self.player.id):
            if ship.trader.id in self.server.sessions:
                self.server.sessions[ship.trader.id].on_ship_enter_sector(sector=target,
                                                                          ship=ship_as_trader)

    def sell_to_port(self, id: int, commodity: CommodityType, amount: int):
        ship = self.galaxy.ships[self.player.ship_id]  # type: Ship
        port = self.galaxy.sectors[ship.sector_id].port  # type: Port

        try:
            amount = int(amount)
        except ValueError:
            self.events.on_invalid_action(error="Not a valid number")
            return

        trading = port.commodity(commodity)
        if not trading.buying:
            self.events.on_invalid_action(error="This port is not buying that commodity")
            return

        if trading.amount < amount:
            self.events.on_invalid_action(error="Not that many available")
            return

        if ship.holds.get(commodity, 0) < amount:
            self.events.on_invalid_action(error="Not enough goods in your holds")
            return

        cost = int(trading.price * amount)
        self.player.credits += cost
        trading.amount -= amount
        ship.remove_from_holds(commodity, amount)

        self.events.on_port_sell(id=id, player=PlayerPublic(self.player))

    def buy_from_port(self, id: int, commodity: CommodityType, amount: int):
        ship = self.galaxy.ships[self.player.ship_id]  # type: Ship
        port = self.galaxy.sectors[ship.sector_id].port  # type: Port

        try:
            amount = int(amount)
        except ValueError:
            self.events.on_invalid_action(error="Not a valid number")
            return

        trading = port.commodity(commodity)
        if trading.buying:
            self.events.on_invalid_action(error="This port is not selling that commodity")
            return

        if trading.amount < amount:
            self.events.on_invalid_action(error="Not that many available")
            return

        cost = int(trading.price * amount)
        if cost > self.player.credits:
            self.events.on_invalid_action(error="Not enough credits available")
            return

        if ship.holds_free < amount:
            self.events.on_invalid_action(error="Not enough holds available")
            return

        self.player.credits -= cost
        trading.amount -= amount
        ship.add_to_holds(commodity, amount)

        self.events.on_port_buy(id=id, player=PlayerPublic(self.player))





