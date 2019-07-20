from tspace.server.models import DamageType, Countermeasure

PLASTIC_CHAFF = Countermeasure(
    id=-1,
    name="Plastic Chaff",
    strengths={DamageType.ENERGY},
    weaknesses={DamageType.EXPLOSIVE},
    strength_bonus=2,
    weakness_penalty=2,
)
METAL_SHRAPNEL = (
    Countermeasure(
        id=-1,
        name="Plastic Shrapnel",
        strengths={DamageType.EXPLOSIVE},
        weaknesses={DamageType.KINETIC},
        strength_bonus=2,
        weakness_penalty=2,
    ),
)
MANEUVERING_THRUSTERS = Countermeasure(
    id=-1,
    name="Maneuvering Thrusters",
    strengths={DamageType.KINETIC},
    weaknesses={DamageType.ENERGY},
    strength_bonus=2,
    weakness_penalty=2,
)


def create() -> Countermeasure:
    breakpoint()
