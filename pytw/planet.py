import random
from collections import namedtuple
from datetime import datetime
import enum
from typing import List

import networkx
from pytw.config import GameConfig
from pytw.graph import gen_hex_center, remove_warps

PORT_NAMES = ["Aegis", "Aeon", "Aeris", "Babylon", "Aeternitas", "Aether", "Alliance", "Alpha", "Amazone", "Ancestor",
              "Anemone", "Angel", "Anomaly", "Apollo", "Arcadia", "Arcadis", "Arch", "Architect", "Ark", "Artemis",
              "Asphodel", "Asteria", "Astraeus", "Athena", "Atlas", "Atmos", "Aura", "Aurora", "Awe", "Azura", "Azure",
              "Baldur", "Beacon", "Blue Moon", "Borealis", "Burrow", "Caelestis", "Canaan", "Century", "Chrono",
              "Chronos", "Crescent", "Curator", "Curiosity", "Data", "Dawn", "Daydream", "Demeter", "Dogma", "Dream",
              "Dune", "Ecstacys", "Eir", "Elyse", "Elysium", "Empyrea", "Ender", "Enigma", "Eos", "Epiphany", "Epitome",
              "Erebus", "Escort", "Eternis", "Eternity", "Exposure", "Fable", "Father", "Fauna", "Felicity", "Flora",
              "Fortuna", "Frontier", "Gaia", "Galaxy", "Genesis", "Genius", "Glory", "Guardian", "Halo", "Heirloom",
              "Helios", "Hemera", "Hera", "Heritage", "Hermes", "Horus", "Hymn", "Hyperion", "Hypnos", "Ignis",
              "Illume", "Inception", "Infinity", "Isis", "Janus", "Juno", "Legacy", "Liberty", "Lore", "Lucent",
              "Lumina", "Luminous", "Luna", "Lunis", "Magni", "Mammoth", "Mani", "Marvel", "Memento", "Minerva",
              "Miracle", "Mother", "Muse", "Mystery", "Mythos", "Nebula", "Nemesis", "Nemo", "Neo", "Nero", "Nimbus",
              "Nott", "Nova", "Novis", "Nox", "Nyx", "Odyssey", "Olympus", "Omega", "Oracle", "Orbital", "Origin",
              "Orphan", "Osiris", "Outlander", "Parable", "Paradox", "Paragon", "Pedigree", "Phantasm", "Phantom",
              "Phenomenon", "Phoenix", "Pilgrim", "Pioneer", "Prism", "Prodigy", "Prometheus", "Prophecy", "Proto",
              "Radiance", "Rebus", "Relic", "Revelation", "Reverie", "Rogue", "Rune", "Saga", "Sancus", "Scout",
              "Selene", "Serenity", "Settler", "Shangris", "Shepherd", "Shu", "Sol", "Solas", "Spectacle", "Specter",
              "Spectrum", "Spire", "Symbolica", "Tartarus", "Terminus", "Terra", "Terran", "Terraria", "Themis",
              "Tiberius", "Titan", "Titanus", "Torus", "Tranquility", "Trivia", "Utopis", "Valhalla", "Vanguard",
              "Vanquish", "Vesta", "Vestige", "Victoria", "Virtue", "Visage", "Voyage", "Vulcan", "Warden", "Yggdrasil",
              "Zeus", "Zion"]
PORT_SUFFIXES = ["", "Station", "Base", "Terminal", "Outpost"] + [str(x) for x in range(0, 9)]

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


class CommodityType(enum.Enum):
    fuel_ore = 1,
    organics = 2,
    equipment = 3


class TradingCommodity:
    def __init__(self, type: CommodityType, amount: int, buying: bool):
        self.type = type
        self.amount = amount
        self.buying = buying
        self.capacity = amount


class PortClass(enum.Enum):
    BBS = (1, True, True, False)
    BSB = (2, True, False, True)
    SBB = (3, False, True, True)
    SSB = (4, False, False, True)
    SBS = (5, False, True, False)
    BSS = (6, True, False, False)
    SSS = (7, False, False, False)
    BBB = (8, True, True, True)

    # noinspection PyInitNewSignature
    def __init__(self, id, buying_fuel_ore, buying_organics, buying_equipment):
        self.id = id
        self.buying = {
            CommodityType.fuel_ore: buying_fuel_ore,
            CommodityType.organics: buying_organics,
            CommodityType.equipment: buying_equipment
        }

    @classmethod
    def by_id(cls, id: int):
        return next(e for e in cls if e.id == id)


def random_port_type(rnd: random.Random) -> PortClass:
    type_chance = rnd.randint(0, 99)
    if type_chance < 20:
        return PortClass.by_id(1)
    elif type_chance < 40:
        return PortClass.by_id(2)
    elif type_chance < 60:
        return PortClass.by_id(3)
    elif type_chance < 70:
        return PortClass.by_id(4)
    elif type_chance < 80:
        return PortClass.by_id(5)
    elif type_chance < 90:
        return PortClass.by_id(6)
    elif type_chance < 95:
        return PortClass.by_id(7)
    else:
        return PortClass.by_id(8)


class Port:

    def __init__(self, sector_id: int, name: str, commodities: List[TradingCommodity]):
        self.commodities = commodities
        self.name = name
        self.sector_id = sector_id


class Sector:
    def __init__(self, sector_id, coords, warps, port: Port):
        self.sector_id = int(sector_id)
        self.warps = [int(x) for x in warps]
        self.planets = []
        self.ships = []
        self.coords = coords
        self.port = port

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

    @property
    def sector(self):
        return self.galaxy.sectors[self.ship.sector_id]

    @property
    def ship(self):
        return self.galaxy.ships[self.ship_id]

    def has_visited(self, sector_id):
        return sector_id in self.visited_sectors

    def visit_sector(self, sector_id):
        self.visited_sectors[int(sector_id)] = datetime.now()

    def teleport(self, new_ship_id):
        self.ship_id = new_ship_id


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
    def __init__(self, config: GameConfig):
        self.config = config
        self.id = config.id
        self.name = config.name

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
        p.ship_id = s.ship_id
        p.visit_sector(sec.sector_id)
        s.move_sector(sec.sector_id)
        sec.enter_ship(s)

        p.visit_sector(self.coords_to_id(0, 0))
        self.players[p.player_id] = p
        return p

    def id_to_coords(self, sector_id):
        return self.sectors[sector_id].coords

    def coords_to_id(self, x, y):
        return self.sector_coords_to_id[(x, y)]

    def _bang_world(self):
        rnd = random.Random(self.config.seed)
        g = gen_hex_center(self.config.diameter)
        remove_warps(g, self.config.warp_density, rnd)
        self._graph = g

        self.sector_coords_to_id = networkx.get_node_attributes(g, "sector_id")
        self.sector_coords_to_id[(0, 0)] = 1

        for n in g.nodes_iter():
            warps = [self.coords_to_id(*target) for target in g.neighbors(n)]
            sector_id = self.coords_to_id(*n)
            port = None
            if rnd.randint(1, 100) >= self.config.port_config.density:
                commodities = []

                ptype = random_port_type(rnd)

                for ctype in CommodityType:
                    buying = ptype.buying[ctype]
                    amount = rnd.randint(200, 2000)
                    commodities.append(TradingCommodity(ctype, amount, buying))

                name = rnd.choice(PORT_NAMES)
                suffix = rnd.choice(PORT_SUFFIXES)
                if suffix:
                    name = " ".join([name, suffix])
                port = Port(sector_id, name, commodities)
            self.sectors[sector_id] = Sector(sector_id, n, warps, port)

    def start(self):
        self._bang_world()
