import asyncio
import json
import sys
from random import choice, randint
from typing import Dict, Callable

from colorclass import Color
from pytw.server import Server


class BotSession:
    def __init__(self, name: str, server: Server):
        self.server = server
        self.name = name
        self.sector = None
        self.actions = None
        self._running = False

    async def on_game_enter(self, player: Dict, **_):

        self.sector = player['ship']['sector']
        self._running = True
        await asyncio.sleep(3)
        while self._running:
            self.actions.move_trader(sector_id=choice([x for x in self.sector['warps'] if x < 10]))
            await asyncio.ensure_future(asyncio.sleep(randint(1, 10)))
        print(f"shutdown: {id(self)}")

    def stop(self):
        self._running = False

    async def on_new_sector(self, sector: Dict, **_):
        self.sector = sector

    async def run(self):
        loop = asyncio.get_event_loop()

        def cb(text):
            data = json.loads(text)
            etype = data['type']
            try:
                loop.create_task(getattr(self, etype)(**data))
            except AttributeError as e:
                # print("unknown attribute: {}", e)
                # sys.stdout.write(Color("{hiblue}OUT: {blue}{text}{/blue}").format(text=text))
                # sys.stdout.write('\n')
                # sys.stdout.flush()
                pass

        in_cb = self.server.join(self.name, cb, debug_network=False)
        self.actions = Actions(in_cb)


class Actions:
    def __init__(self, cb: Callable[[str], None]):
        self.cb = cb

    def __getattr__(self, item):
        def f(**kwargs):
            data = {'type': item}
            data.update(kwargs)
            self.cb(json.dumps(data))
        return f