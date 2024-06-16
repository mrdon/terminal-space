from __future__ import annotations

import typing
from collections import defaultdict

from tspace.client.stream import Fragment
from tspace.common.models import (
    CommodityType,
    GameConfigPublic,
    PlanetPublic,
    TraderShipPublic,
    PortPublic,
    SectorPublic,
    ShipPublic,
    PlayerPublic,
    TradingCommodityPublic,
    TraderPublic,
)

if typing.TYPE_CHECKING:
    from tspace.client.game import Game


class GameConfig:
    def __init__(self, client: GameConfigPublic):
        self.id = client.id
        self.name = client.name
        self.diameter = client.diameter


class Planet:
    def __init__(self, game: Game, planet: PlanetPublic):
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

    def update(self, planet: PlanetPublic):
        self.name = planet.name
        self.owner_id = planet.owner.id if planet.owner else None
        self.planet_type = planet.planet_type

        self.fuel_ore = planet.fuel_ore
        self.organics = planet.organics
        self.equipment = planet.equipment

    @property
    def owner(self):
        return self._game.traders[self.owner_id] if self.owner_id else None


class TradingCommodity:
    def __init__(self, client: TradingCommodityPublic):
        self.type = CommodityType[client.type]
        self.price: int = None
        self.capacity: int = None
        self.amount: int = None
        self.buying: bool = False
        self.update(client)

    def update(self, client: TradingCommodityPublic):
        self.price = client.price if client.price is not None else self.price
        self.capacity = (
            client.capacity if client.capacity is not None else self.capacity
        )
        self.amount = client.amount if client.amount is not None else self.amount
        self.buying = client.buying


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

    def __init__(self, game: Game, client: PortPublic):
        self._game = game
        self.id = client.id
        self.sector_id = client.sector_id
        self.name: str = ""
        self.commodities: dict[CommodityType, TradingCommodity] = {}
        self.update(client)

    def update(self, client: PortPublic):
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
        return self._game.sectors.get(self.sector_id)

    @property
    def class_name(self):
        c = {c_type: c_value.buying for c_type, c_value in self.commodities.items()}

        name = []
        for ctype in CommodityType:
            name.append("B" if c[ctype] else "S")

        return "".join(name)

    @property
    def class_name_colored(self) -> list[Fragment]:
        line = []
        for c in self.class_name:
            line.append(Fragment("cyan", c) if c == "B" else Fragment("green", c))
        return line

    @property
    def class_number(self):
        return self.CLASSES[self.class_name]


class Trader:
    def __init__(self, game: Game, client: TraderPublic):
        self._game = game
        self.id = client.id
        self.name: str = ""

    def update(self, client: TraderPublic):
        self.name = client.name


class TraderShip:
    def __init__(self, game: Game, client: TraderShipPublic):
        self.id = client.id
        self._game = game
        self.name: str = ""
        self.trader_id: int = 0

    def update(self, client: TraderShipPublic):
        self.name = client.name
        self.trader_id = client.trader.id

    @property
    def trader(self) -> Trader | None:
        return self._game.traders.get(self.trader_id)


class Sector:
    def __init__(self, game: Game, client: SectorPublic):
        self.id = client.id
        self._game = game
        self.update(client)

    def update(self, client: SectorPublic):
        self.warps = client.warps

        self.port_ids = [port.id for port in client.ports]
        self.trader_ship_ids = [ship.id for ship in client.ships]
        self.planet_ids = [p.id for p in client.planets]

    @property
    def ports(self) -> list[Port]:
        return [self._game.ports[port_id] for port_id in self.port_ids]

    @property
    def ships(self) -> list[TraderShip]:
        return [
            self._game.trader_ships.get(ship_id) for ship_id in self.trader_ship_ids
        ]

    @property
    def planets(self) -> list[Planet]:
        return [self._game.planets.get(id) for id in self.planet_ids]


class Ship:
    def __init__(self, game: Game, client: ShipPublic):
        self._game = game
        self.id = client.id
        self.name: str = ""
        self.holds_capacity: int = 0
        self.sector_id: int = 0

        self.holds: dict[CommodityType, int] = defaultdict(lambda: 0)
        self.update(client)

    def update(self, client: ShipPublic):
        self.name = client.name
        self.type = client.type
        self.holds_capacity = client.holds_capacity

        self.holds.update(client.holds)
        self.sector_id = client.sector.id if client.sector else None

    @property
    def sector(self) -> Sector | None:
        return self._game.sectors.get(self.sector_id)

    @property
    def holds_free(self):
        return self.holds_capacity - sum(self.holds.values())


class Player:
    def __init__(self, game: Game, client: PlayerPublic):
        self._game = game
        self.id = client.id
        self.visited: set[int] = set()
        self.credits: int = 0
        self.name: str = ""
        self.ship_id: int = 0
        self.port_id: int = 0
        self.update(client)

    def update(self, client: PlayerPublic):
        self.credits = client.credits
        self.name = client.name
        self.ship_id = client.ship.id if client.ship else None

    @property
    def ship(self) -> Ship | None:
        return None if not self.ship_id else self._game.ships.get(self.ship_id)

    @property
    def port(self) -> Port | None:
        return None if not self.port_id else self._game.ports.get(self.port_id)

    @property
    def sector(self) -> Sector | None:
        return None if not self.ship_id else self.ship.sector
