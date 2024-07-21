from __future__ import annotations

from enum import Enum, auto


class SceneId(Enum):
    MAIN_MENU = auto()
    GAME = auto()
    BATTLE = auto()
    QUIT = auto()
    PREVIOUS = auto()


class Scene:
    async def run(self) -> SceneId:
        pass