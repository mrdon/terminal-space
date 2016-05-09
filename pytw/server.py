from typing import Callable

from pytw.config import GameConfig
from pytw.moves import ShipMoves, ServerEvents
from pytw.planet import Galaxy
from pytw.util import CallMethodOnEventType


class Server:
    def __init__(self, config: GameConfig):
        self.config = config
        self.game = Galaxy(config)
        self.game.start()

    def join(self, name, callback: Callable[[str], None]) -> Callable[[str], None]:
        player = self.game.add_player(name)

        events = ServerEvents(callback)
        moves = ShipMoves(player, self.game, events)
        prefix = None if not self.config.debug_network else "IN "
        return CallMethodOnEventType(moves, prefix=prefix)
