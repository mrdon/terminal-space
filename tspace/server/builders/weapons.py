from tspace.server.models import Weapon, DamageType

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


def create() -> Weapon:
    breakpoint()
