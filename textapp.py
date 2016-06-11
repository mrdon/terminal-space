import sys

import asyncio
from functools import partial
from threading import Thread

from pytw.config import GameConfig
from pytw.server import Server
from pytw_ansi.session import Session
from pytw_ansi.stream import Terminal
from pytw_bot.session import BotSession


class TestApp:
    def __init__(self):
        self.config = GameConfig(1, "Test Game", diameter=10, seed="test", debug_network=False)
        self.server = Server(self.config)
        self.out = Terminal()
        self.session = Session(self.config, self.out, self.server)
        self.bots = [BotSession("Bot {}".format(x), self.server) for x in range(5)]

    def run_bots(self, loop: asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        for bot in self.bots:
            loop.call_soon(bot.run)
        loop.run_forever()

    def run(self, loop: asyncio.AbstractEventLoop):
        main_t = Thread(target=self.session.start)
        main_t.start()
        bot_t = Thread(target=partial(self.run_bots, loop))
        bot_t.start()
        main_t.join()
        for bot in self.bots:
            bot.stop()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    TestApp().run(loop)
