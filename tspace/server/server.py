from typing import Awaitable
from typing import Callable
from typing import Dict

from tspace.server.config import GameConfig
from tspace.server.moves import GameConfigPublic
from tspace.server.moves import PlayerPublic
from tspace.server.moves import ShipMoves, ServerEvents
from tspace.server.galaxy import Galaxy
from tspace.server.util import CallMethodOnEventType


class Server:
    def __init__(self, config: GameConfig):
        self.config = config
        self.sessions: Dict[int, ServerEvents] = {}
        self.game = Galaxy(config)
        self.game.start()

    async def join(
        self, name, callback: Callable[[str], Awaitable[None]]
    ) -> Callable[[str], Awaitable[None]]:
        player = self.game.add_player(name)
        events = ServerEvents(callback)
        moves = ShipMoves(self, player, self.game, events)
        await events.on_game_enter(
            player=PlayerPublic(player),
            config=GameConfigPublic(self.config, len(self.game.sectors)),
        )
        self.sessions[player.id] = events
        await moves.broadcast_player_enter_sector(player)

        return CallMethodOnEventType(moves)
