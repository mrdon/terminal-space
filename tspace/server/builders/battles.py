from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, List

from tspace.server.util import AutoIncrementId

from tspace.server.models import Sector, Player, Battle, Ship

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


def create(game: Galaxy, attacker: Ship, target: Ship) -> Battle:
    battle = Battle(
        game=game,
        id=autoid.incr(),
        sector_id=attacker.sector_id,
        attacker_ship_id=attacker.id,
        target_ship_id=target.id,
        )
    game.battles[battle.id] = battle
    attacker.battle_id = battle.id
    target.battle_id = battle.id

    return battle
