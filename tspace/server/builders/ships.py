from __future__ import annotations

from typing import TYPE_CHECKING

from tspace.common.models import ShipType
from tspace.server.builders import weapons, countermeasures
from tspace.server.util import AutoIncrementId

from tspace.server.models import Ship, DamageType

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


MERCHANT_CRUISER = ShipType(
    name="Merchant Cruiser",
    cost=41300,
    holds_initial=200,
    holds_max=75,
    warp_cost=2,
    has_scanner_slot=True,
    has_shield_slot=True,
    weapons_max=3,
    countermeasures_max=3,
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
    )
    ship.add_weapon(weapons.create(game, DamageType.EXPLOSIVE))
    ship.add_weapon(weapons.create(game, DamageType.KINETIC))
    ship.add_weapon(weapons.create(game, DamageType.ENERGY))

    ship.add_countermeasure(countermeasures.create(game, DamageType.EXPLOSIVE))
    ship.add_countermeasure(countermeasures.create(game, DamageType.KINETIC))
    ship.add_countermeasure(countermeasures.create(game, DamageType.ENERGY))
    game.ships[ship.id] = ship
    return ship
