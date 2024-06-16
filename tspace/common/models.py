from __future__ import annotations

from enum import Enum, StrEnum

from pydantic import BaseModel


class ShipType(BaseModel):
    name: str
    cost: int
    holds_initial: int
    holds_max: int
    warp_cost: int
    weapons_max: int
    countermeasures_max: int
    has_shield_slot: bool
    has_scanner_slot: bool


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
    port: PortPublic | None


class TraderPublic(BaseModel):
    id: int
    name: str


class TraderShipPublic(BaseModel):
    id: int
    name: str
    type: ShipType
    trader: TraderPublic


class ShipPublic(BaseModel):
    id: int
    name: str
    holds_capacity: int
    holds: dict[CommodityType, int]
    sector: SectorPublic
    type: str


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
