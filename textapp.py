import sys

from pytw.config import GameConfig
from pytw.server import Server
from pytw_ansi.session import Session
from pytw_ansi.stream import TerminalOutput


class TestApp:
    def __init__(self):
        self.config = GameConfig(1, "Test Game", diameter=10, seed="test", debug_network=True)
        self.server = Server(self.config)
        self.out = TerminalOutput()
        self.session = Session(self.config, sys.stdin, self.out, self.server)

    def run(self):
        self.session.start()


if __name__ == '__main__':
    import colorclass
    print("foo", colorclass.list_tags())
    TestApp().run()
