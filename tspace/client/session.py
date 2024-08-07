import asyncio
import inspect
from asyncio import CancelledError
from asyncio import Future
from asyncio import Task
from typing import Callable, Awaitable
from typing import Optional

from tspace.client import models, sector_prompt, port_prompt
from tspace.client.game import Game
from tspace.client.instant_cmd import InstantCmd
from tspace.client.logging import log
from tspace.client.models import GameConfig
from tspace.client.prompts import PromptTransition
from tspace.client.prompts import PromptType
from tspace.client.terminal import Terminal
from tspace.client.util import EventBus
from tspace.common.models import GameConfigPublic, PlayerPublic, PortPublic
from tspace.common.actions import SectorActions, PortActions, BattleActions


class Session:
    def __init__(self, term: Terminal):
        self.term = term

        self.game: Optional[Game] = None
        self.action_sink = None

        self.bus: Optional[EventBus] = None
        self.prompt = self._start_no_prompt()
        self.prompt_task: Optional[Task] = None

    async def _start(self, action_sink: Callable[[str], Awaitable[None]]):
        context = {
            k: v
            for k, v in inspect.getmembers(models, inspect.isclass)
            if k.endswith("Client")
        }
        self.bus = EventBus(self, context=context, sender=action_sink)

        waiting_prompt = None
        while True:
            try:
                if self.prompt is None:
                    break
                waiting_prompt = self.prompt
                self.prompt_task = asyncio.create_task(self.prompt.cmdloop())
                await self.prompt_task
            except CancelledError:
                pass
            except PromptTransition as e:
                self.bus.remove_event_listener(self.prompt)
                if waiting_prompt and waiting_prompt == self.prompt:
                    if e.next == PromptType.SECTOR:
                        self.prompt = self._start_sector_prompt()
                    elif e.next == PromptType.PORT:
                        self.prompt = self._start_port_prompt()
                    elif e.next == PromptType.BATTLE:
                        await self._start_battle()
                    elif e.next == PromptType.QUIT:
                        break
                    elif e.next == PromptType.NONE:
                        self.prompt = self._start_no_prompt()

    async def on_game_enter(self, player: PlayerPublic, config: GameConfigPublic):
        log.info("on game enter!!!!!!!!!!!!!")
        self.game = Game(GameConfig(config))
        self.game.update_player(player)

        prompt = self._start_sector_prompt()
        # prompt.print_sector(self.game.player.ship.sector)
        self.prompt = prompt
        self.prompt_task.cancel()

    async def on_port_enter(self, port: PortPublic, player: PlayerPublic):
        p = self.game.update_port(port)
        self.game.update_player(player)
        self.game.player.port_id = p.id

        self.prompt = self._start_port_prompt()
        self.prompt_task.cancel()

    async def on_port_exit(self, port: PortPublic, player: PlayerPublic):
        self.game.update_port(port)
        self.game.update_player(player)
        self.game.player.port_id = None

        self.prompt = self._start_sector_prompt()
        self.prompt_task.cancel()

    async def on_invalid_action(self, error: str):
        self.term.error(error)
        self.prompt = self._start_sector_prompt()
        self.prompt_task.cancel()

    def _quit(self):
        self.prompt = None
        self.prompt_task.cancel()

    def _start_sector_prompt(self):
        actions = self.bus.wire_sending_methods(SectorActions)
        prompt = sector_prompt.Prompt(self.game, actions, term=self.term)
        prompt.print_sector()
        self.bus.append_event_listener(prompt)
        return prompt

    def _start_port_prompt(self):
        actions = self.bus.wire_sending_methods(PortActions)
        prompt = port_prompt.Prompt(self.game, actions, self.term)
        events = port_prompt.Events(prompt)
        self.bus.append_event_listener(events)
        return prompt

    def _start_battle(self):
        actions = self.bus.wire_sending_methods(BattleActions)

        prompt = battle_prompt.Prompt(self.game, actions, self.term)
        events = battle_prompt.Events(prompt)
        self.bus.append_event_listener(events)
        return prompt

    def _start_no_prompt(self):
        prompt = InstantCmd(self.term)

        async def raise_quit(*_):
            raise PromptTransition(PromptType.QUIT)

        prompt.literal("q", default=False)(raise_quit)
        return prompt


class NoOpPrompt:
    async def cmdloop(self):
        fut = Future()
        await fut

    def __str__(self):
        return "No prompt"
