from typing import List, Set

from pytw.moves import ShipMoves, Events, Actions
from pytw.planet import Galaxy, Player, Sector, ShipType, Ship


class Server:
    def __init__(self):
        self.game = Galaxy(1, "foo", 5)
        self.game.start()

    def join(self, name, callback: Events) -> Actions:
        player = self.game.add_player(name)
        return Actions(player, self.game, callback)





