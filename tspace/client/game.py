from __future__ import annotations
from typing import Dict
from typing import List

import networkx as nx

from tspace.client.models import GameConfig
from tspace.client.models import Planet
from tspace.client.models import PlanetClient
from tspace.client.models import Player
from tspace.client.models import PlayerClient
from tspace.client.models import Port
from tspace.client.models import PortClient
from tspace.client.models import Sector
from tspace.client.models import SectorClient
from tspace.client.models import Ship
from tspace.client.models import ShipClient
from tspace.client.models import Trader
from tspace.client.models import TraderClient
from tspace.client.models import TraderShip
from tspace.client.models import TraderShipClient


class Game:
    def __init__(self, config: GameConfig):
        self.config = config
        self.sectors: List[Sector] = [None] * (config.sectors_count + 1)
        self.trader_ships: Dict[int, TraderShip] = {}
        self.ships: Dict[int, Ship] = {}
        self.ports: Dict[int, Port] = {}
        self.traders: Dict[int, Trader] = {}
        self.planets: Dict[int, Planet] = {}
        self.player: Player = None

    # noinspection PyUnresolvedReferences
    def update_player(self, client: PlayerClient) -> Player:
        if self.player:
            self.player.update(client)
        else:
            self.player = Player(self, client)

        if client.ship:
            self.update_ship(client.ship)

        return self.player

    def update_ship(self, client: ShipClient) -> Ship:
        if client.id in self.ships:
            self.ships[client.id].update(client)
        else:
            self.ships[client.id] = Ship(self, client)

        if client.sector:
            self.update_sector(client.sector)
            self.ships[client.id].sector_id = client.sector.id
            self.player.visited.add(client.sector.id)

        return self.ships[client.id]

    def update_sector(self, client: SectorClient) -> Sector:
        sector = self.sectors[client.id] if client.id in self.sectors else None
        if sector:
            sector.update(client)
        else:
            self.sectors[client.id] = Sector(self, client)

        if client.port:
            self.update_port(client.port)

        if client.ships:
            for ship in client.ships:
                self.update_trader_ship(ship)

        if client.planets:
            for planet in client.planets:
                self.update_planet(planet)

        return self.sectors[client.id]

    def update_trader_ship(self, client: TraderShipClient) -> TraderShip:
        if client.id in self.trader_ships:
            self.trader_ships[client.id].update(client)
        else:
            self.trader_ships[client.id] = TraderShip(self, client)

        if client.trader:
            self.update_trader(client.trader)

        return self.trader_ships[client.id]

    def update_port(self, client: PortClient) -> Port:
        if client.sector_id in self.ports:
            self.ports[client.sector_id].update(client)
        else:
            self.ports[client.sector_id] = Port(self, client)

        return self.ports[client.sector_id]

    def update_trader(self, client: TraderClient) -> Trader:
        if client.id in self.traders:
            self.traders[client.id].update(client)
        else:
            self.traders[client.id] = Trader(self, client)

        return self.traders[client.id]

    def update_planet(self, client: PlanetClient) -> Planet:
        if client.id in self.planets:
            self.planets[client.id].update(client)
        else:
            self.planets[client.id] = Planet(self, client)

        return self.planets[client.id]

    def plot_course(self, from_id: int, to_id: int) -> List[Sector]:
        g = self._gen_graph()
        steps: List[int] = nx.shortest_path(g, from_id, to_id)
        return [self.sectors[x] for x in steps]

    def _gen_graph(self) -> nx.Graph:
        g = nx.Graph(directed=True)

        for sector in (sector for sector in self.sectors if sector):
            g.add_node(sector.id)
            for warp in sector.warps:
                g.add_edge(sector.id, warp)

        return g
