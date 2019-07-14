import sys

import asyncio
from functools import partial
from threading import Thread

from pytw.config import GameConfig
from pytw.server import Server
from pytw_textui.app import TwApplication
from pytw_textui.session import Session
from pytw_textui.stream import Terminal
from pytw_bot.session import BotSession


class TestApp:
    def __init__(self):
        self.config = GameConfig(1, "Test Game", diameter=10, seed="test", debug_network=False)
        self.server = Server(self.config)
        self.app = TwApplication()
        self.out = Terminal(self.app.buffer)
        self.session = Session(self.config, self.out, self.server)

    def run(self):
        main_t = Thread(target=self.session.start)
        main_t.start()
        self.app.run()
        main_t.join()


if __name__ == '__main__':
    TestApp().run()
