from typing import Awaitable, TypeVar
from typing import Callable
from typing import Dict

from tspace.common.rpc import ClientAndServer
from tspace.server.config import GameConfig
from tspace.server.galaxy import Galaxy
from tspace.server.moves import GameConfigPublic
from tspace.server.moves import PlayerPublic
from tspace.server.moves import ShipMoves, ServerEvents

T = TypeVar("T")


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

        api = ClientAndServer(callback)

        events = api.build_client(ServerEvents)

        moves = ShipMoves(self, player, self.game, events)
        api.register_methods(moves)

        await events.on_game_enter(
            player=player.to_public(),
            config=self.config.to_public(),
        )
        self.sessions[player.id] = events
        await moves._broadcast_player_enter_sector(player)

        return api.on_incoming
