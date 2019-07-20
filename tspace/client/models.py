from __future__ import annotations

import enum
import typing
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from tspace.client.stream import Fragment

if typing.TYPE_CHECKING:
    from tspace.client.game import Game


@dataclass
class GameConfigClient:
    id: int
    name: str
    diameter: int
    sectors_count: int


class GameConfig:
    def __init__(self, client: GameConfigClient):
        self.id = client.id
        self.name = client.name
        self.diameter = client.diameter
        self.sectors_count = client.sectors_count


@dataclass
class PlanetClient:
    id: int
    name: str
    regions: List
    planet_type: str
    fuel_ore: int
    organics: int
    equipment: int
    fighters: int
    owner: TraderClient


class Planet:
    def __init__(self, game: Game, planet: PlanetClient):
        self._game = game
        self.id: int = planet.id
        self.name: str = ""
        self.owner_id: int = 0
        self.planet_type: str = ""

        self.fuel_ore: int = 0
        self.organics: int = 0
        self.equipment: int = 0
        self.fighters: int = 0
        self.update(planet)

    def update(self, planet: PlanetClient):
        self.name = planet.name
        self.owner_id = planet.owner.id if planet.owner else None
        self.planet_type = planet.planet_type

        self.fuel_ore = planet.fuel_ore
        self.organics = planet.organics
        self.equipment = planet.equipment
        self.fighters = planet.fighters

    @property
    def owner(self):
        return self._game.traders[self.owner_id] if self.owner_id else None


@dataclass
class TradingCommodityClient:
    type: str
    buying: bool
    amount: int
    capacity: int
    price: int


class TradingCommodity:
    def __init__(self, client: TradingCommodityClient):
        self.type = CommodityType[client.type]
        self.price: int = None
        self.capacity: int = None
        self.amount: int = None
        self.buying: bool = False
        self.update(client)

    def update(self, client: TradingCommodityClient):
        self.price = client.price if client.price is not None else self.price
        self.capacity = (
            client.capacity if client.capacity is not None else self.capacity
        )
        self.amount = client.amount if client.amount is not None else self.amount
        self.buying = client.buying


class CommodityType(enum.Enum):
    fuel_ore = "Fuel Ore"
    organics = "Organics"
    equipment = "Equipment"


@dataclass
class PortClient:
    id: int
    sector_id: int
    name: str
    commodities: List[TradingCommodityClient]


class Port:
    CLASSES = {
        "BBS": 1,
        "BSB": 2,
        "SBB": 3,
        "SSB": 4,
        "SBS": 5,
        "BSS": 6,
        "SSS": 7,
        "BBB": 8,
    }

    def __init__(self, game: Game, client: PortClient):
        self._game = game
        self.id = client.id
        self.sector_id = client.sector_id
        self.name: str = ""
        self.commodities: Dict[CommodityType, TradingCommodity] = {}
        self.update(client)

    def update(self, client: PortClient):
        self.name = client.name

        if client.commodities:
            for commodity in client.commodities:
                commodity_type = CommodityType[commodity.type]
                if commodity_type in self.commodities:
                    self.commodities[commodity_type].update(commodity)
                else:
                    self.commodities[commodity_type] = TradingCommodity(commodity)

    @property
    def sector(self):
        return self._game.sectors[self.sector_id]

    @property
    def class_name(self):
        c = {c_type: c_value.buying for c_type, c_value in self.commodities.items()}

        name = []
        for ctype in CommodityType:
            name.append("B" if c[ctype] else "S")

        return "".join(name)

    @property
    def class_name_colored(self) -> List[Fragment]:
        line = []
        for c in self.class_name:
            line.append(Fragment("cyan", c) if c == "B" else Fragment("green", c))
        return line

    @property
    def class_number(self):
        return self.CLASSES[self.class_name]


@dataclass
class TraderClient:
    id: int
    name: str


class Trader:
    def __init__(self, game: Game, client: TraderClient):
        self._game = game
        self.id = client.id
        self.name: str = ""

    def update(self, client: TraderClient):
        self.name = client.name


@dataclass
class TraderShipClient:
    id: int
    name: str
    trader: TraderClient


class TraderShip:
    def __init__(self, game: Game, client: TraderShipClient):
        self.id = client.id
        self._game = game
        self.name: str = ""
        self.trader_id: int = 0

    def update(self, client: TraderShipClient):
        self.name = client.name
        self.trader_id = client.trader.id

    @property
    def trader(self) -> Optional[Trader]:
        return self._game.traders.get(self.trader_id)


@dataclass
class SectorClient:
    id: int
    coords: Tuple[int, int]
    warps: List[int]
    ports: List[PortClient]
    ships: List[TraderShipClient]
    planets: List[PlanetClient]


class Sector:
    def __init__(self, game: Game, client: SectorClient):
        self.id = client.id
        self._game = game
        self.port_ids: List[int] = []
        self.warps: List[int] = []
        self.coords: Tuple[int, int] = (0, 0)
        self.trader_ship_ids: List[int] = []
        self.planet_ids: List[int] = []
        self.update(client)

    def update(self, client: SectorClient):
        self.warps = client.warps
        self.coords = client.coords

        self.port_ids = [port.id for port in client.ports]
        self.trader_ship_ids = [ship.id for ship in client.ships]
        self.planet_ids = [p.id for p in client.planets]

    @property
    def ports(self) -> List[Port]:
        return [self._game.ports[port_id] for port_id in self.port_ids]

    @property
    def ships(self) -> List[TraderShip]:
        return [
            self._game.trader_ships.get(ship_id) for ship_id in self.trader_ship_ids
        ]

    @property
    def planets(self) -> List[Planet]:
        return [self._game.planets.get(id) for id in self.planet_ids]


@dataclass
class ShipClient:
    id: int
    name: str
    holds_capacity: int
    holds: Dict[str, int]
    sector: SectorClient


class Ship:
    def __init__(self, game: Game, client: ShipClient):
        self._game = game
        self.id = client.id
        self.name: str = ""
        self.holds_capacity: int = 0
        self.sector_id: int = 0

        self.holds: Dict[CommodityType, int] = defaultdict(lambda: 0)
        self.update(client)

    def update(self, client: ShipClient):
        self.name = client.name
        self.holds_capacity = client.holds_capacity

        self.holds.update({CommodityType[k]: v for k, v in client.holds.items()})
        self.sector_id = client.sector.id if client.sector else None

    @property
    def sector(self) -> Optional[Sector]:
        return None if not self.sector_id else self._game.sectors[self.sector_id]

    @property
    def holds_free(self):
        return self.holds_capacity - sum(self.holds.values())


@dataclass
class PlayerClient:
    id: int
    name: int
    credits: int
    ship: ShipClient


class Player:
    def __init__(self, game: Game, client: PlayerClient):
        self._game = game
        self.id = client.id
        self.visited: Set[int] = set()
        self.credits: int = 0
        self.name: str = ""
        self.ship_id: int = 0
        self.port_id: int = 0
        self.update(client)

    def update(self, client: PlayerClient):
        self.credits = client.credits
        self.name = client.name
        self.ship_id = client.ship.id if client.ship else None

    @property
    def ship(self) -> Optional[Ship]:
        return None if not self.ship_id else self._game.ships.get(self.ship_id)

    @property
    def port(self) -> Optional[Port]:
        return None if not self.port_id else self._game.ports.get(self.port_id)

    @property
    def sector(self) -> Optional[Sector]:
        return None if not self.ship_id else self.ship.sector
