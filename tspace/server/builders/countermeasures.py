from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from tspace.server.util import AutoIncrementId
from tspace.server.models import DamageType, Countermeasure

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()

PLASTIC_CHAFF = Countermeasure(
    id=-1,
    name="Plastic Chaff",
    strengths={DamageType.ENERGY},
    weaknesses={DamageType.EXPLOSIVE},
    strength_bonus=2,
    weakness_penalty=2,
)
METAL_SHRAPNEL = Countermeasure(
    id=-1,
    name="Plastic Shrapnel",
    strengths={DamageType.EXPLOSIVE},
    weaknesses={DamageType.KINETIC},
    strength_bonus=2,
    weakness_penalty=2,
)
MANEUVERING_THRUSTERS = Countermeasure(
    id=-1,
    name="Maneuvering Thrusters",
    strengths={DamageType.KINETIC},
    weaknesses={DamageType.ENERGY},
    strength_bonus=2,
    weakness_penalty=2,
)


def create(game: Galaxy, strength_type: DamageType) -> Countermeasure:
    if strength_type == DamageType.ENERGY:
        template = PLASTIC_CHAFF
    elif strength_type == DamageType.KINETIC:
        template = MANEUVERING_THRUSTERS
    elif strength_type == DamageType.EXPLOSIVE:
        template = METAL_SHRAPNEL
    else:
        breakpoint()
        raise ValueError()
    countermeasure = dataclasses.replace(template, id=autoid.incr())
    game.countermeasures[countermeasure.id] = countermeasure
    return countermeasure
