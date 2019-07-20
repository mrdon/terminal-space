from __future__ import annotations

from typing import TYPE_CHECKING

from tspace.server.models import Player
from tspace.server.util import AutoIncrementId

if TYPE_CHECKING:
    from tspace.server.models import Galaxy

autoid = AutoIncrementId()


def create(game: Galaxy, name: str) -> Player:
    player = Player(
        game, autoid.incr(), name, credits=game.config.player.initial_credits
    )
    game.players[player.id] = player
    return player
