import enum
from collections import defaultdict
from typing import Tuple, List, Set, Dict

from termcolor import colored


class TradingCommodityClient:
    def __init__(self, type: str, buying: bool, amount: int, capacity: int, price: int):
        self.price = price
        self.capacity = capacity
        self.amount = amount
        self.buying = buying
        self.type = CommodityType[type]


class CommodityType(enum.Enum):
    fuel_ore = "Fuel Ore"
    organics = "Organics"
    equipment = "Equipment"


class PortClient:

    CLASSES = {
        "BBS": 1,
        "BSB": 2,
        "SBB": 3,
        "SSB": 4,
        "SBS": 5,
        "BSS": 6,
        "SSS": 7,
        "BBB": 8
    }

    def __init__(self, sector_id: int, name: str, commodities: List[TradingCommodityClient]):
        self.commodities = commodities
        self.name = name
        self.sector_id = sector_id

    @property
    def class_name(self):
        c = {c.type: c.buying for c in self.commodities}

        name = []
        for ctype in CommodityType:
            name.append("B" if c[ctype] else "S")

        return "".join(name)

    @property
    def class_name_colored(self):
        line = []
        for c in self.class_name:
            line.append(colored(c, 'cyan', attrs=['bold']) if c == 'B' else colored(c, 'green'))
        return "".join(line)

    @property
    def class_number(self):
        return self.CLASSES[self.class_name]


class SectorClient:
    def __init__(self, id: int, coords: Tuple[int, int], warps: List[int], port: PortClient):
        self.port = port
        self.warps = warps
        self.coords = coords
        self.id = id
        self.traders = None  # todo
        self.ships = None  # todo


class ShipClient:
    def __init__(self, id: int, name: str, holds_capacity: int, holds: Dict[str, int], sector: SectorClient):
        self.holds_capacity = holds_capacity
        self.holds = defaultdict(lambda: 0)
        self.holds.update({CommodityType[k]: v for k, v in holds.items()})
        self.sector = sector
        self.name = name
        self.id = id

    @property
    def holds_free(self):
        return self.holds_capacity - sum(self.holds.values())


class PlayerClient:

    def __init__(self, id: int, name: str, credits: int, ship: ShipClient, visited: Set[int]):
        self.credits = credits
        self.visited = visited
        self.ship = ship
        self.name = name
        self.id = id

    def update(self, player):
        self.credits = player.credits
        self.ship = player.ship
