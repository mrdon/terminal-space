from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

from tspace.common.models import ShipType
from tspace.server.builders import drones
from tspace.server.builders.drones import FIGHTER
from tspace.server.util import AutoIncrementId

from tspace.server.models import Ship, DroneStack

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


MERCHANT_CRUISER = ShipType(
    name="Merchant Cruiser",
    cost=41300,
    holds_initial=200,
    holds_max=75,
    warp_cost=2,
    drone_stack_max=3,
    attack=2,
    defense=3,
    initiative=5,
)


def create() -> Ship:
    breakpoint()


def create_initial(game: Galaxy, name: str, player_id: int, sector_id: int):
    ship = Ship(
        game,
        autoid.incr(),
        MERCHANT_CRUISER,
        name,
        player_id=player_id,
        sector_id=sector_id,
        drones=[],
    )

    for _ in range(ship.ship_type.drone_stack_max):
        drones.create_initial(ship, drone_type=FIGHTER, count=game.rnd.randint(1, 50))

    game.ships[ship.id] = ship
    return ship
