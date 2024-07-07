from typing import Any, Optional

from tspace.common.models import GameConfigPublic
from tspace.server.models import SessionContext


class PortConfig:
    def __init__(self, density: int = 40):
        self.density = density


class PlayerConfig:
    def __init__(self, initial_sector_id: int = 1, initial_credits: int = 2000):
        self.initial_credits = initial_credits
        self.initial_sector_id = initial_sector_id


class GameConfig:
    def __init__(
        self,
        id: int,
        name: str,
        diameter: int = 50,
        seed: Optional[Any] = None,
        port: PortConfig = PortConfig(),
        player: PlayerConfig = PlayerConfig(),
        debug_network: bool = False,
        warp_density: int = 3.5,
        sectors_count: int = 0,
    ):
        self.player = player
        self.warp_density = warp_density
        self.debug_network = debug_network
        self.seed = seed
        self.port = port
        self.diameter = diameter
        self.name = name
        self.id = id
        self.sectors_count = sectors_count

    def to_public(self, context: SessionContext) -> GameConfigPublic:
        return GameConfigPublic(
            id=self.id,
            name=self.name,
            diameter=self.diameter,
            sectors_count=self.sectors_count,
        )
