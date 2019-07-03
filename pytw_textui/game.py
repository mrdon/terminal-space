from pytw_textui.models import GameConfigClient
from pytw_textui.models import PlayerClient


class Game:
    def __init__(self, config: GameConfigClient, player: PlayerClient):
        self.config = config
        self.sectors = []
        self.player = player
        self.traders = {}



