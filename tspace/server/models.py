from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import List, Dict, Iterable, Tuple
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel

from tspace.common.models import (
    PlayerPublic,
    TraderPublic,
    ShipPublic,
    TradingCommodityPublic,
    PortPublic,
    SectorPublic,
    PlanetPublic,
    TraderShipPublic,
    CommodityType,
)

if TYPE_CHECKING:
    from tspace.server.galaxy import Galaxy


class Planet:
    def __init__(
        self,
        game: Galaxy,
        id: int,
        planet_type: str,
        name: str,
        owner_id: Optional[int],
    ):
        self.game: Galaxy = game
        self.name = name
        self.id = id
        self.owner_id = owner_id
        self.planet_type = planet_type

        self.fuel_ore = 0
        self.organics = 0
        self.equipment = 0
        self.fighters = 0

    def to_public(self) -> PlanetPublic:
        return PlanetPublic(
            id=self.id,
            name=self.name,
            owner=self.owner.to_trader() if self.owner else None,
            planet_type=self.planet_type,
            fuel_ore=self.fuel_ore,
            organics=self.organics,
            equipment=self.equipment,
        )

    @property
    def owner(self):
        return self.game.players[self.owner_id] if self.owner_id else None


@dataclass
class CommodityCost:
    sell_cost: int
    buy_offer: float


COMMODITY_COSTS = {
    CommodityType.fuel_ore: CommodityCost(1, 1.5),
    CommodityType.organics: CommodityCost(2, 3),
    CommodityType.equipment: CommodityCost(4, 6),
}


class TradingCommodity:
    def __init__(self, type: CommodityType, amount: int, buying: bool):
        self.type: CommodityType = type
        self.amount = amount
        self.buying = buying
        self.capacity = amount

    def to_public(self) -> TradingCommodityPublic:
        return TradingCommodityPublic(
            amount=self.amount,
            capacity=self.capacity,
            buying=self.buying,
            type=self.type.name,
            price=self.price,
        )

    @property
    def price(self):
        cost = COMMODITY_COSTS[self.type]
        if self.buying:
            return round(
                cost.buy_offer + ((self.amount / self.capacity) * cost.buy_offer) / 2,
                2,
            )
        else:
            return round(
                cost.sell_cost - ((self.amount / self.capacity) * cost.sell_cost) / 2,
                2,
            )


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
            CommodityType.equipment: buying_equipment,
        }

    @classmethod
    def by_id(cls, id: int):
        return next(e for e in cls if e.id == id)


class Port:
    def __init__(
        self, id: int, sector_id: int, name: str, commodities: List[TradingCommodity]
    ):
        self.id = id
        self.commodities = commodities
        self.name = name
        self.sector_id = sector_id

    def to_public(self) -> PortPublic:
        return PortPublic(
            id=self.id,
            name=self.name,
            sector_id=self.sector_id,
            commodities=[c.to_public() for c in self.commodities],
        )

    def commodity(self, type: CommodityType):
        return next(c for c in self.commodities if c.type == type)


class Sector:
    def __init__(
        self, game: Galaxy, id: int, coords: Tuple[int, int], warps: List[int]
    ):
        self.game: Galaxy = game
        self.id = int(id)
        self.warps = [int(x) for x in warps]
        self.planet_ids: List[int] = []
        self.ship_ids = []
        self.coords = coords
        self.port_ids = []

    def to_public(self) -> SectorPublic:

        ports = [port.to_public() for port in self.ports]
        for port in ports:
            for c in port.commodities:
                c.amount = None
                c.capacity = None
                c.price = None

        return SectorPublic(
            id=self.id,
            warps=self.warps,
            ports=ports,
            ships=[ship.to_trader() for ship in self.ships],
            planets=[planet.to_public() for planet in self.planets],
        )

    def can_warp(self, sector_id):
        return sector_id in self.warps

    def exit_ship(self, ship):
        self.ship_ids.remove(ship.id)

    def enter_ship(self, ship):
        self.ship_ids.append(ship.id)

    @property
    def ships(self):
        return [self.game.ships[id] for id in self.ship_ids]

    @property
    def planets(self):
        return [self.game.planets[id] for id in self.planet_ids]

    @property
    def ports(self):
        return [self.game.ports[id] for id in self.port_ids]


class Player:
    def __init__(self, game, id: int, name: str, credits: int):
        self.name = name
        self.id: int = id
        self.galaxy = game
        self.credits: int = credits
        self.ship_id = None
        self.port_id = None
        self.sector_id = None

    def to_public(self):
        return PlayerPublic(
            id=self.id,
            name=self.name,
            ship=self.ship.to_public(),
            credits=self.credits,
            sector=self.sector.to_public(),
            port=None if not self.port else self.port.to_public(),
        )

    def to_trader(self) -> TraderPublic:
        return TraderPublic(
            id=self.id,
            name=self.name,
        )

    @property
    def sector(self):
        return self.galaxy.sectors[self.sector_id]

    @sector.setter
    def sector(self, value: Sector):
        self.sector_id = value.id

    @property
    def ship(self):
        return self.galaxy.ships[self.ship_id]

    @property
    def port(self):
        return self.galaxy.ports[self.port_id] if self.port_id else None

    @port.setter
    def port(self, value: Port):
        self.port_id = value.sector_id if value else None

    def visit_sector(self, sector_id):
        self.sector_id = sector_id

    def teleport(self, new_ship_id):
        self.ship_id = new_ship_id


class Battle:
    def __init__(self, game: Galaxy, id: int, sector_id: int, player_ids: list[int]):
        self.id = id
        self.game = game
        self.sector_id = sector_id
        self.player_ids = player_ids


class DamageType(enum.Enum):
    ENERGY = "Energy"
    KINETIC = "Kinetic"
    EXPLOSIVE = "Explosive"


@dataclass
class Weapon:
    id: int
    name: str
    accuracy_bonus: int
    damage_min: int
    damage_max: int
    damage_type: DamageType


@dataclass
class Countermeasure:
    id: int
    name: str
    strengths: Iterable[DamageType]
    strength_bonus: int
    weaknesses: Iterable[DamageType]
    weakness_penalty: int


class Ship:
    def __init__(
        self,
        game: Galaxy,
        id: int,
        ship_type: ShipType,
        name: str,
        player_id: int,
        sector_id: int,
    ):
        self.id = id
        self.type = ship_type
        self.name = name
        self.player_owner_id = player_id
        self.player_id = player_id
        self.holds_capacity = ship_type.holds_initial
        self.holds: Dict[CommodityType, int] = {}
        self.ship_type = ship_type
        self.sector_id = sector_id
        self.game = game
        self.weapon_ids: List[int] = []
        self.countermeasure_ids: List[int] = []

    def to_public(self) -> ShipPublic:
        return ShipPublic(
            id=self.id,
            name=self.name,
            holds_capacity=self.holds_capacity,
            holds={t: val for t, val in self.holds.items()},
            sector=(
                self.game.sectors[self.sector_id].to_public()
                if self.sector_id
                else None
            ),
            type=self.ship_type.name,
        )

    def to_trader(self) -> TraderShipPublic:
        return TraderShipPublic(
            id=self.id,
            name=self.name,
            type=self.ship_type,
            trader=self.player.to_trader(),
        )

    def move_sector(self, sector_id):
        self.sector_id = sector_id

    def add_to_holds(self, commodity_type: CommodityType, amount: int):
        self.holds[commodity_type] = self.holds.get(commodity_type, 0) + amount

    @property
    def holds_free(self):
        return self.holds_capacity - sum(self.holds.values())

    @property
    def player(self):
        return self.game.players[self.player_id]

    @property
    def sector(self):
        return self.game.sectors[self.sector_id]

    @property
    def weapons(self) -> List[Weapon]:
        return [self.game.weapons[id] for id in self.weapon_ids]

    @property
    def countermeasures(self) -> List[Countermeasure]:
        return [self.game.countermeasures[id] for id in self.countermeasure_ids]

    def remove_from_holds(self, commodity_type: CommodityType, amount: int):
        self.holds[commodity_type] -= amount

    def add_weapon(self, weapon: Weapon):
        if len(self.weapon_ids) < self.ship_type.weapons_max:
            self.weapon_ids.append(weapon.id)
        else:
            raise ValueError("Cannot add any more weapons")

    def add_countermeasure(self, countermeasure: Countermeasure):
        if len(self.countermeasure_ids) < self.ship_type.countermeasures_max:
            self.countermeasure_ids.append(countermeasure.id)
        else:
            raise ValueError("Cannot add any more countermeasures")
