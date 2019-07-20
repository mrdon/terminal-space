from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, List

from tspace.server.util import AutoIncrementId

from tspace.server.models import Sector

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


def create(game: Galaxy, id: int, coords: Tuple[int, int], warps: List[int]) -> Sector:
    sector = Sector(game, id, coords, warps)
    game.sectors[sector.id] = sector
    return sector
