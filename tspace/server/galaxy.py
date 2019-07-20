from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict

import networkx

from tspace.server.graph import gen_hex_center, remove_warps
from tspace.server.models import Sector, Player, Ship, Planet, Port
from tspace.server.builders import planets, players, ports, sectors, ships

if TYPE_CHECKING:
    from tspace.server.config import GameConfig


class Galaxy:
    def __init__(self, config: GameConfig):
        self.config = config
        self.id = config.id
        self.name = config.name

        self.sectors: Dict[int, Sector] = {}
        self.ports: Dict[int, Port] = {}
        self.sector_coords_to_id = {}
        self.players: Dict[int, Player] = {}
        self.ships: Dict[int:Ship] = {}
        self.planets: Dict[int, Planet] = {}
        self._graph = None

        self.rnd = random.Random(self.config.seed)

    def add_player(self, name):

        p = players.create(self, name)

        sec = self.sectors[self.config.player.initial_sector_id]
        ship = ships.create_initial(self, "Foo", p.id, sec.id)

        p.ship_id = ship.id
        p.visit_sector(sec.id)
        ship.move_sector(sec.id)
        sec.enter_ship(ship)
        return p

    def id_to_coords(self, sector_id):
        return self.sectors[sector_id].coords

    def coords_to_id(self, x, y):
        return self.sector_coords_to_id[(x, y)]

    def _bang_world(self):
        g = gen_hex_center(self.config.diameter)
        remove_warps(g, self.config.warp_density, self.rnd)
        self._graph = g

        self.sector_coords_to_id = networkx.get_node_attributes(g, "sector_id")
        self.sector_coords_to_id[(0, 0)] = 1

        for n in g.nodes_iter():
            warps = [self.coords_to_id(*target) for target in g.neighbors(n)]
            sector_id = self.coords_to_id(*n)
            sector = sectors.create(self, sector_id, n, warps)

            if self.rnd.randint(1, 100) >= self.config.port.density:
                port = ports.create(self, sector_id)
                sector.port_ids.append(port.id)

            if self.rnd.randint(1, 2) == 1:
                for x in range(int(self.rnd.gauss(4.5, 1.5))):
                    planet = planets.create(self, None)
                    sector.planet_ids.append(planet.id)

    def start(self):
        self._bang_world()
