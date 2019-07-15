from typing import Any, Optional


class PortConfig:
    def __init__(self, density: int = 40):
        self.density = density


class PlayerConfig:
    def __init__(
        self,
        initial_sector_id: int = 1,
        initial_ship_type: str = "merchant_cruiser",
        initial_credits: int = 2000,
    ):
        self.initial_credits = initial_credits
        self.initial_ship_type = initial_ship_type
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
    ):
        self.player = player
        self.warp_density = warp_density
        self.debug_network = debug_network
        self.seed = seed
        self.port = port
        self.diameter = diameter
        self.name = name
        self.id = id
