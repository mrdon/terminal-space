from __future__ import annotations
from tspace.server.constants import PORT_NAMES, PLANET_SUFFIXES
from typing import TYPE_CHECKING

from tspace.server.util import AutoIncrementId
from tspace.server.models import Planet

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


def create(game: Galaxy, owner_id: int) -> Planet:
    base_name = game.rnd.choice(PORT_NAMES)
    suffix = game.rnd.choice(PLANET_SUFFIXES)
    name = f"{base_name} {suffix}".strip()
    type = game.rnd.choice(["V", "M"])
    planet = Planet(game, autoid.incr(), type, name, owner_id)
    game.planets[planet.id] = planet
    return planet
