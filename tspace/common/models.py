from __future__ import annotations

from enum import StrEnum, auto, Enum

from pydantic import BaseModel


class ShipType(BaseModel):
    name: str
    cost: int
    holds_initial: int
    holds_max: int
    warp_cost: int
    drone_stack_max: int
    attack: int
    defense: int
    initiative: int


class DroneType(BaseModel):
    name: str
    symbol_right: str
    symbol_left: str
    leadership: int
    attack: int
    defense: int
    speed: int
    initiative: int
    damage_range: tuple[int, int]


class CommodityType(StrEnum):
    fuel_ore = "Fuel Ore"
    organics = "Organics"
    equipment = "Equipment"


class GameConfigPublic(BaseModel):
    id: int
    name: str
    diameter: int
    sectors_count: int


class PlayerPublic(BaseModel):
    id: int
    name: str
    ship: ShipPublic
    credits: int
    sector: SectorPublic
    port: PortPublic | None = None


class TraderPublic(BaseModel):
    id: int
    name: str


class DroneStackPublic(BaseModel):
    drone_type: DroneType
    size: int


class RelativeStrength(StrEnum):
    OVERWHELMING = "Overwhelming", 90
    VERY_STRONG = "Very Strong", 80
    STRONG = "Strong", 60
    EVEN = "Even", 50
    WEAK = "Weak", 30
    VERY_WEAK = "Very Weak", 0

    def __new__(cls, value, percentage: int):
        member = str.__new__(cls, value)
        member._value_ = value
        member.percentage = percentage
        return member


class TraderShipPublic(BaseModel):
    id: int
    name: str
    type: ShipType
    trader: TraderPublic
    relative_strength: RelativeStrength
    in_battle: bool = False


class CombatantPublic(BaseModel):
    ship: TraderShipPublic
    drones: list[DroneStackPublic]


class ShipPublic(BaseModel):
    id: int
    name: str
    holds_capacity: int
    holds: dict[CommodityType, int]
    drones: list[DroneStackPublic]
    sector: SectorPublic
    type: str
    battle: BattlePublic | None = None


class TradingCommodityPublic(BaseModel):
    amount: int | None
    capacity: int | None
    buying: bool
    type: str
    price: float | None


class PortPublic(BaseModel):
    id: int
    name: str
    sector_id: int
    commodities: list[TradingCommodityPublic]


class SectorPublic(BaseModel):
    id: int
    warps: list[int]
    ports: list[PortPublic]
    ships: list[TraderShipPublic]
    planets: list[PlanetPublic]


class PlanetPublic(BaseModel):
    id: int
    name: str
    owner: TraderPublic | None
    planet_type: str
    fuel_ore: int
    organics: int
    equipment: int


class BattlePublic(BaseModel):
    id: int
    sector: SectorPublic
    attacker: ShipPublic
    target: CombatantPublic
