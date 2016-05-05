import random
from collections import namedtuple
from datetime import datetime
import enum

import networkx
from pytw.graph import gen_hex_center, remove_warps


Cost = namedtuple("Cost", ["credits", "fuel_ore", "organics", "equipment", "colonists", "time", "citadel_level_min"])


class Region:
    def __init__(self, name, level, cost_initial, cost_upgrade):
        self.name = name
        self.level = level
        self.cost_initial = cost_initial
        self.cost_upgrade = cost_upgrade


class FuelOreRegion(Region):
    costs = {
        1: Cost(credits=1000, fuel_ore=1000, organics=1000, equipment=1000, colonists=1000, time=1,
                citadel_level_min=1),
        2: Cost(credits=2000, fuel_ore=2000, organics=2000, equipment=2000, colonists=2000, time=2,
                citadel_level_min=1),
        3: Cost(credits=3000, fuel_ore=3000, organics=3000, equipment=3000, colonists=3000, time=4,
                citadel_level_min=1),
        4: Cost(credits=4000, fuel_ore=4000, organics=4000, equipment=4000, colonists=4000, time=7,
                citadel_level_min=1),
        5: Cost(credits=5000, fuel_ore=5000, organics=5000, equipment=5000, colonists=5000, time=11,
                citadel_level_min=1)
    }

    def __init__(self, level):
        super(FuelOreRegion, self).__init__("Fuel Ore", level, 1000, 2000)
        self.output = 50


PlanetTypeArgs = namedtuple("PlanetTypeArgs", ["name", "fuel_ore_boost", "organics_boost", "equipment_boost"])


class PlanetType(PlanetTypeArgs, enum.Enum):
    M = PlanetTypeArgs(name="M",
                       fuel_ore_boost=10,
                       organics_boost=10,
                       equipment_boost=10)


class Planet:
    MAX_REGIONS = 10

    def __init__(self, planet_type, planet_id, name, owner_id):
        self.name = name
        self.id = planet_id
        self.owner_id = owner_id
        self.planet_type = planet_type
        self.regions = []

        self.fuel_ore = 0
        self.organics = 0
        self.equipment = 0
        self.fighters = 0

    def add_region(self, region):
        if len(self.regions) == self.MAX_REGIONS:
            raise ValueError("Region limit reached")

        self.regions.append(region)


class Sector:
    def __init__(self, sector_id, coords, warps):
        self.sector_id = int(sector_id)
        self.warps = [int(x) for x in warps]
        self.planets = []
        self.ships = []
        self.coords = coords

    def can_warp(self, sector_id):
        return sector_id in self.warps

    def exit_ship(self, ship):
        self.ships.remove(ship.ship_id)

    def enter_ship(self, ship):
        self.ships.append(ship.ship_id)


class Player:
    def __init__(self, game, player_id, name):
        self.name = name
        self.player_id = player_id
        self.galaxy = game
        self.ship_id = None
        self.visited_sectors = {}

    def has_visited(self, sector_id):
        return sector_id in self.visited_sectors

    def visit_sector(self, sector_id):
        self.visited_sectors[int(sector_id)] = datetime.now()

    def teleport(self, new_ship_id):
        self.current_ship_id = new_ship_id


ShipTypeArgs = namedtuple("ShipTypeArgs", ["name", "cost", "fighters_max", "fighters_per_wave", "holds_initial",
                                           "holds_max", "warp_cost", "offensive_odds", "defensive_odds"])


class ShipType(ShipTypeArgs, enum.Enum):
    MERCHANT_CRUISER = ShipTypeArgs(name="Merchant Cruiser",
                                    cost=41300,
                                    fighters_max=2500,
                                    fighters_per_wave=750,
                                    holds_initial=20,
                                    holds_max=75,
                                    warp_cost=2,
                                    offensive_odds=1,
                                    defensive_odds=1)


class Ship:
    def __init__(self, ship_type, ship_id, name, player_id, sector_id):
        self.name = name
        self.ship_id = ship_id
        self.player_owner_id = player_id
        self.player_id = player_id
        self.ship_type = ship_type
        self.sector_id = sector_id

    def move_sector(self, sector_id):
        self.sector_id = sector_id


class Galaxy:
    def __init__(self, game_id, name, diameter):
        self.id = game_id
        self.name = name
        self.diameter = diameter

        self.sectors = {}
        self.sector_coords_to_id = {}
        self.players = {}
        self.ships = {}
        self._graph = None

    def add_player(self, name):
        p = Player(self, 1, name)
        sec = self.sectors[1]
        s = Ship(ShipType.MERCHANT_CRUISER, 1, 'Foo', p.player_id, 1)
        self.ships[s.ship_id] = s
        p.visit_sector(sec.sector_id)
        s.move_sector(sec.sector_id)
        sec.enter_ship(s)
        p.current_ship_id = 1

        p.visit_sector(self.coords_to_id(0, 0))
        self.players[p.player_id] = p
        return p

    def id_to_coords(self, sector_id):
        return self.sectors[sector_id].coords

    def coords_to_id(self, x, y):
        return self.sector_coords_to_id[(x, y)]

    def _bang_world(self):
        density = 3.5
        seed = random.seed()
        g = gen_hex_center(self.diameter)
        print("removing warps")
        remove_warps(g, density, seed)
        self._graph = g

        self.sector_coords_to_id = networkx.get_node_attributes(g, "sector_id")
        self.sector_coords_to_id[(0, 0)] = 1

        print("building sectors")
        for n in g.nodes_iter():
            warps = [self.coords_to_id(*target) for target in g.neighbors(n)]
            sector_id = self.coords_to_id(*n)
            self.sectors[sector_id] = Sector(sector_id, n, warps)

        print("Banged")

    def start(self):
        self._bang_world()
