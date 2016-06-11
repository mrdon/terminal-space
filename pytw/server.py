from typing import Callable
from typing import Dict

from pytw.config import GameConfig
from pytw.moves import ShipMoves, ServerEvents
from pytw.planet import Galaxy
from pytw.util import CallMethodOnEventType


class Server:
    def __init__(self, config: GameConfig):
        self.config = config
        self.sessions = {}  # type: Dict[int, ShipMoves]
        self.game = Galaxy(config)
        self.game.start()

    def join(self, name, callback: Callable[[str], None], debug_network=None) -> Callable[[str], None]:
        player = self.game.add_player(name)
        events = ServerEvents(callback)
        moves = ShipMoves(self, player, self.game, events)
        self.sessions[player.id] = events
        moves.broadcast_player_enter_sector(player)

        debug_network = debug_network if debug_network is not None else self.config.debug_network
        prefix = None if not debug_network else "IN "
        return CallMethodOnEventType(moves, prefix=prefix)
