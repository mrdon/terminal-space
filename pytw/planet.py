from collections import namedtuple
import enum


Cost = namedtuple("Cost", ["credits", "fuel_ore", "organics", "equipment", "colonists", "time", "citadel_level_min"])


class Region:

    def __init__(self, name, level, cost_initial, cost_upgrade):
        self.name = name
        self.level = level
        self.cost_initial = cost_initial
        self.cost_upgrade = cost_upgrade


class FuelOreRegion(Region):

    costs = {
        1: Cost(credits=1000, fuel_ore=1000, organics=1000, equipment=1000, colonists=1000, time=1, citadel_level_min=1),
        2: Cost(credits=2000, fuel_ore=2000, organics=2000, equipment=2000, colonists=2000, time=2, citadel_level_min=1),
        3: Cost(credits=3000, fuel_ore=3000, organics=3000, equipment=3000, colonists=3000, time=4, citadel_level_min=1),
        4: Cost(credits=4000, fuel_ore=4000, organics=4000, equipment=4000, colonists=4000, time=7, citadel_level_min=1),
        5: Cost(credits=5000, fuel_ore=5000, organics=5000, equipment=5000, colonists=5000, time=11, citadel_level_min=1)
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

    def __init__(self, sector_id, warps):
        self.sector_id = sector_id
        self.warps = warps
        self.planets = []
        self.ships = []


class Player:

    def __init__(self, player_id, name):
        self.name = name
        self.id = player_id


ShipTypeArgs = namedtuple("ShipTypeArgs", ["name", "cost", "fighters_max", "fighters_per_wave", "holds_initial",
                                           "holds_max", "warp_cost", "offensive_odds", "defensive_odds"])
class ShipType(ShipTypeArgs, enum.Enum):

    MERCHANT = ShipTypeArgs(name="Merchant Cruiser",
                            cost=41300,
                            fighters_max=2500,
                            fighters_per_wave=750,
                            holds_initial=20,
                            holds_max=75,
                            warp_cost=2,
                            offensive_odds=1,
                            defensive_odds=1)

class Ship:
    def __init__(self, ship_type, ship_id, name, player_id):
        self.name = name
        self.ship_id = ship_id
        self.player_id = player_id
        self.ship_type = ship_type


class Game:
    def __init__(self, game_id, name):
        self.id = game_id
        self.name = name

        self.sectors = {}
        self.players = {}

    def _bang_world(self, radius):
        for x in [(radius-abs(x-int(radius/2))) for x in range(radius)]:
            for y in range(radius-x):
                print(' '),
        for y in range(x):
            print(' * '),
        print('')

    def start(self):
        self._bang_world(5)


Game('1', 'asdf').start()
