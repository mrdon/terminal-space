import asyncio
import inspect
from asyncio import CancelledError
from asyncio import Future
from asyncio import Lock
from asyncio import Task
from typing import Awaitable
from typing import Callable
from typing import Optional

from pytw.util import CallMethodOnEventType
from pytw_textui import models
from pytw_textui import sector_prompt, port_prompt
from pytw_textui.game import Game
from pytw_textui.models import GameConfig
from pytw_textui.models import GameConfigClient
from pytw_textui.models import PlayerClient
from pytw_textui.models import PortClient
from pytw_textui.models import SectorClient
from pytw_textui.prompts import PromptTransition, PromptType
from pytw_textui.stream import Terminal


class Session:
    def __init__(self, term: Terminal):
        self.term = term
        context = {k: v for k, v in inspect.getmembers(models, inspect.isclass) if k.endswith("Client")}
        self.event_caller = CallMethodOnEventType(self, context=context)
        self.game: Optional[Game] = None
        self.action_sink = None

        self.prompt = NoOpPrompt()
        self.prompt_task: Optional[Task] = None

    async def start(self, action_sink: Callable[[str], Awaitable[None]]):
        self.action_sink = action_sink

        while True:
            try:
                self.prompt_task = asyncio.create_task(self.prompt.cmdloop())
                await self.prompt_task
            except CancelledError:
                pass
            except PromptTransition as e:
                self.event_caller.remove(self.prompt)
                if e.next == PromptType.SECTOR:
                    self.prompt = self.start_sector_prompt(self.action_sink)
                elif e.next == PromptType.PORT:
                    self.prompt = self.start_port_prompt(self.action_sink)
                elif e.next == PromptType.QUIT:
                    break
                elif e.next == PromptType.NONE:
                    self.prompt = NoOpPrompt()

    async def on_game_enter(self, player: PlayerClient, config: GameConfigClient):
        # print("on game enter!!!!!!!!!!!!!")
        self.game = Game(GameConfig(config))
        self.game.update_player(player)

        prompt = self.start_sector_prompt(self.action_sink)
        # prompt.print_sector(self.game.player.ship.sector)
        self.prompt = prompt
        self.prompt_task.cancel()

    async def on_new_sector(self, sector: SectorClient):
        s = self.game.update_sector(sector)

        self.game.player.ship.sector_id = sector.id
        self.game.player.visited.add(s.id)

        self.prompt = self.start_sector_prompt(self.action_sink)
        self.prompt_task.cancel()

    async def on_port_enter(self, port_client: PortClient):
        port = self.game.update_port(port_client)
        self.game.player.port_id = port.sector_id

    async def on_port_exit(self, port_client: PortClient):
        self.game.update_port(port_client)
        self.game.player.port_id = None

    async def on_invalid_action(self, error: str):
        self.term.error(error)
        self.prompt = self.start_sector_prompt(self.action_sink)
        self.prompt_task.cancel()

    def start_sector_prompt(self, action_sink: Callable[[str], None]):
        actions = sector_prompt.Actions(action_sink)
        prompt = sector_prompt.Prompt(self.game, actions, term=self.term)
        prompt.print_sector()
        self.event_caller.append(prompt)
        return prompt

    def start_port_prompt(self, action_sink: Callable[[str], None]):
        actions = port_prompt.Actions(action_sink)
        prompt = port_prompt.Prompt(self.game.player, actions, self.term)
        events = port_prompt.Events(prompt)
        self.event_caller.append(events)
        return prompt


class NoOpPrompt:

    async def cmdloop(self):
        fut = Future()
        await fut
