from __future__ import annotations

from typing import TYPE_CHECKING

from tspace.common.models import ShipType, DroneType
from tspace.server.util import AutoIncrementId

from tspace.server.models import Ship, DroneStack

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


FIGHTER = DroneType(
    name="Fighter",
    symbol_right="\u257E",
    symbol_left="\u257C",
    leadership=10,
    attack=1,
    defense=1,
    speed=5,
    initiative=4,
    damage_range=(1, 3),
)


def create_initial(ship: Ship, drone_type: DroneType, count: int) -> DroneStack:
    assert len(ship.drones) < ship.ship_type.drone_stack_max
    stack = DroneStack(drone_type, count)
    ship.drones.append(stack)
    return stack
