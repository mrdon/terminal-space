from functools import partial
from typing import Callable

from pytw.config import GameConfig
from pytw.moves import ShipMoves, ServerEvents, ServerActions
from pytw.planet import Galaxy
from pytw.util import call_type, CallMethodOnEventType


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
        return CallMethodOnEventType(ServerActions(moves), prefix=prefix)
