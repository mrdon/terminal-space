from typing import Callable
from typing import Dict

from pytw.config import GameConfig
from pytw.moves import GameConfigPublic
from pytw.moves import PlayerPublic
from pytw.moves import ShipMoves, ServerEvents
from pytw.planet import Galaxy
from pytw.util import CallMethodOnEventType


class Server:
    def __init__(self, config: GameConfig):
        self.config = config
        self.sessions = {}  # type: Dict[int, ShipMoves]
        self.game = Galaxy(config)
        self.game.start()

    async def join(self, name, callback: Callable[[str], None]) -> Callable[[str], None]:
        player = self.game.add_player(name)
        events = ServerEvents(callback)
        moves = ShipMoves(self, player, self.game, events)
        await events.on_game_enter(player=PlayerPublic(player), config=GameConfigPublic(self.config, len(self.game.sectors)))
        self.sessions[player.id] = events
        await moves.broadcast_player_enter_sector(player)

        return CallMethodOnEventType(moves)
