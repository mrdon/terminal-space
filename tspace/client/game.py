from __future__ import annotations

from collections import defaultdict

import networkx as nx

from tspace.client.logging import log
from tspace.client.models import GameConfig
from tspace.client.models import Planet
from tspace.client.models import Player
from tspace.client.models import Port
from tspace.client.models import Sector
from tspace.client.models import Ship
from tspace.client.models import Trader
from tspace.client.models import TraderShip
from tspace.common.models import (
    PlanetPublic,
    PortPublic,
    TraderPublic,
    TraderShipPublic,
    SectorPublic,
    ShipPublic,
)


class Game:
    def __init__(self, config: GameConfig):
        self.config = config
        self.sectors: dict[int, Sector] = {}
        self.trader_ships: dict[int, TraderShip] = {}
        self.ships: dict[int, Ship] = {}
        self.ports: dict[int, Port] = {}
        self.traders: dict[int, Trader] = {}
        self.planets: dict[int, Planet] = {}
        self.player: Player = None

    # noinspection PyUnresolvedReferences
    def update_player(self, client: PlayerPublic) -> Player:
        if self.player:
            self.player.update(client)
        else:
            self.player = Player(self, client)

        if client.ship:
            self.update_ship(client.ship)

        return self.player

    def update_ship(self, client: ShipPublic) -> Ship:
        if client.id in self.ships:
            self.ships[client.id].update(client)
        else:
            self.ships[client.id] = Ship(self, client)

        if client.sector:
            self.update_sector(client.sector)
            self.ships[client.id].sector_id = client.sector.id
            self.player.visited.add(client.sector.id)

        return self.ships[client.id]

    def update_sector(self, client: SectorPublic) -> Sector:
        sector = self.sectors[client.id] if client.id in self.sectors else None
        if sector:
            sector.update(client)
        else:
            log.info(f"Adding sector : {client.id}")
            self.sectors[client.id] = Sector(self, client)

        if client.ports:
            for port in client.ports:
                self.update_port(port)

        if client.ships:
            for ship in client.ships:
                self.update_trader_ship(ship)

        if client.planets:
            for planet in client.planets:
                self.update_planet(planet)

        for warp_id in (x for x in client.warps if x not in self.sectors):
            log.info(f"Adding warp sector : {warp_id}")
            self.sectors[warp_id] = Sector(
                self, SectorPublic(id=warp_id, warps=[], ports=[], ships=[], planets=[])
            )

        return self.sectors[client.id]

    def update_trader_ship(self, client: TraderShipPublic) -> TraderShip:
        if client.id in self.trader_ships:
            self.trader_ships[client.id].update(client)
        else:
            self.trader_ships[client.id] = TraderShip(self, client)

        if client.trader:
            self.update_trader(client.trader)

        return self.trader_ships[client.id]

    def update_port(self, client: PortPublic) -> Port:
        if client.id in self.ports:
            self.ports[client.id].update(client)
        else:
            self.ports[client.id] = Port(self, client)

        return self.ports[client.id]

    def update_trader(self, client: TraderPublic) -> Trader:
        if client.id in self.traders:
            self.traders[client.id].update(client)
        else:
            self.traders[client.id] = Trader(self, client)

        return self.traders[client.id]

    def update_planet(self, client: PlanetPublic) -> Planet:
        if client.id in self.planets:
            self.planets[client.id].update(client)
        else:
            self.planets[client.id] = Planet(self, client)

        return self.planets[client.id]

    def plot_course(self, from_id: int, to_id: int) -> list[Sector]:
        g = self._gen_graph()
        steps: list[int] = nx.shortest_path(g, from_id, to_id)
        return [self.sectors[x] for x in steps]

    def _gen_graph(self) -> nx.Graph:
        g = nx.Graph(directed=True)

        for sector in (sector for sector in self.sectors.values() if sector):
            g.add_node(sector.id)
            for warp in sector.warps:
                g.add_edge(sector.id, warp)

        return g
