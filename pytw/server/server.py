from typing import Awaitable
from typing import Callable
from typing import Dict

from pytw.server.config import GameConfig
from pytw.server.moves import GameConfigPublic
from pytw.server.moves import PlayerPublic
from pytw.server.moves import ShipMoves, ServerEvents
from pytw.server.planet import Galaxy
from pytw.server.util import CallMethodOnEventType


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
