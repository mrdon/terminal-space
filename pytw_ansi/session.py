from typing import Callable

from pytw.config import GameConfig
from pytw.server import Server
from pytw.util import CallMethodOnEventType
from pytw_ansi import sector_prompt, port_prompt
from pytw_ansi.models import PlayerClient
from pytw_ansi.prompts import PromptTransition, PromptType


class Session:
    def __init__(self, config: GameConfig, stdin, stdout, server: Server):
        self.server = server
        self.stdin = stdin
        self.stdout = stdout
        self.config = config
        prefix = None if not self.config.debug_network else "OUT"
        self.event_caller = CallMethodOnEventType(self, prefix)
        self.player = None  # type: PlayerClient
        self.server = server

    def start(self):
        action_sink = self.server.join("Bob", self.event_caller)
        prompt = self.start_sector_prompt(action_sink)
        self.stdout.nl(2)
        prompt.print_sector(self.player.ship.sector)

        while True:
            try:
                prompt.cmdloop()
            except PromptTransition as e:
                if e.next == PromptType.SECTOR:
                    prompt = self.start_sector_prompt(action_sink)
                elif e.next == PromptType.PORT:
                    prompt = self.start_port_prompt(action_sink)
                elif e.next == PromptType.QUIT:
                    exit(0)

    def on_game_enter(self, player: PlayerClient):
        self.player = player

    def start_sector_prompt(self, action_sink: Callable[[str], None]):
        actions = sector_prompt.Actions(action_sink)
        prompt = sector_prompt.Prompt(self.player, actions, self.stdin, self.stdout)
        events = sector_prompt.Events(prompt)
        self.event_caller.target = events
        return prompt

    def start_port_prompt(self, action_sink: Callable[[str], None]):
        actions = port_prompt.Actions(action_sink)
        prompt = port_prompt.Prompt(self.player, actions, self.stdin, self.stdout)
        events = port_prompt.Events(prompt)
        self.event_caller.target = events
        return prompt

