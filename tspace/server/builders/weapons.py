from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from tspace.server.models import Weapon, DamageType
from tspace.server.util import AutoIncrementId

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()

MINING_LASER = Weapon(
    id=-1,
    name="Mining Laser",
    accuracy_bonus=1,
    damage_type=DamageType.ENERGY,
    damage_max=3,
    damage_min=1,
)
CONCUSSION_MISSILE = Weapon(
    id=-1,
    name="Concussion Missile",
    accuracy_bonus=1,
    damage_type=DamageType.EXPLOSIVE,
    damage_max=3,
    damage_min=1,
)
RAILGUN = Weapon(
    id=-1,
    name="Railgun",
    accuracy_bonus=1,
    damage_type=DamageType.KINETIC,
    damage_max=3,
    damage_min=1,
)


def create(game: Galaxy, type: DamageType) -> Weapon:
    if type == DamageType.ENERGY:
        weapon_template = MINING_LASER
    elif type == DamageType.KINETIC:
        weapon_template = RAILGUN
    elif type == DamageType.EXPLOSIVE:
        weapon_template = CONCUSSION_MISSILE
    else:
        breakpoint()
        raise ValueError()
    weapon = dataclasses.replace(weapon_template, id=autoid.incr())
    game.weapons[weapon.id] = weapon
    return weapon
