from typing import Any, Optional


class PortConfig:
    def __init__(self,
                 density: int = 40,
                 ):
        self.density = density


class GameConfig:
    def __init__(self,
                 id: int,
                 name: str,
                 diameter: int = 50,
                 seed: Optional[Any] = None,
                 port_config: PortConfig = PortConfig(),
                 debug_network: bool = False
                 ):
        self.debug_network = debug_network
        self.seed = seed
        self.port_config = port_config
        self.diameter = diameter
        self.name = name
        self.id = id
