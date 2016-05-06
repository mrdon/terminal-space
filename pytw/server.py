from functools import partial
from typing import Callable

from pytw.moves import ShipMoves, ServerEvents, ServerActions
from pytw.planet import Galaxy
from pytw.util import call_type


class Server:
    def __init__(self):
        self.game = Galaxy(1, "foo", 5)
        self.game.start()

    def join(self, name, callback: Callable[[str], None]) -> Callable[[str], None]:
        player = self.game.add_player(name)

        events = ServerEvents(callback)
        moves = ShipMoves(player, self.game, events)
        return partial(call_type, ServerActions(moves))
