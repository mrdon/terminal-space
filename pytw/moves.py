from typing import Callable

from pytw.planet import Galaxy, Player, Sector, Ship
from pytw.util import methods_to_json


class PlayerPublic:
    def __init__(self, player: Player):
        self.id = player.player_id
        self.name = player.name
        self.ship = ShipPublic(player.ship, player.sector)
        self.visited = list(player.visited_sectors.keys())


class ShipPublic:
    def __init__(self, ship: Ship, sector: Sector):
        self.id = ship.ship_id
        self.name = ship.name
        self.type = ship.ship_type
        self.sector = SectorPublic(sector)


class SectorPublic:
    def __init__(self, sector: Sector):
        self.id = sector.sector_id
        self.coords = sector.coords
        self.warps = sector.warps
        self.traders = None  # todo
        self.ships = None  # todo


@methods_to_json()
class ServerEvents:
    def __init__(self, target: Callable[[str], None]):
        self.target = target

    def on_game_enter(self, player: PlayerPublic):
        pass

    def on_new_sector(self, sector: SectorPublic):
        pass

    def on_invalid_action(self, error: str):
        pass


class ShipMoves:

    def __init__(self, player, galaxy: Galaxy, events: ServerEvents):
        super().__init__()
        self.galaxy = galaxy
        self.player = player
        self.events = events

        self.events.on_game_enter(player=PlayerPublic(player))

    def move_sector(self, target_sector_id):
        target = self.galaxy.sectors[target_sector_id]
        ship = self.galaxy.ships[self.player.ship_id]
        ship_sector = self.galaxy.sectors[ship.sector_id]

        if ship.player_id != self.player.player_id:
            self.events.on_invalid_action(error="Ship not occupied by player")
            return

        if not ship_sector.can_warp(target.sector_id):
            self.events.on_invalid_action(error="Target sector not adjacent to ship")
            return

        ship_sector.exit_ship(ship)
        target.enter_ship(ship)
        ship.move_sector(target.sector_id)
        self.player.visit_sector(target.sector_id)
        self.events.on_new_sector(sector=SectorPublic(target))


class ServerActions:
    def __init__(self, moves: ShipMoves):
        self.moves = moves

    def move_trader(self, sector_id: int):
        self.moves.move_sector(sector_id)
