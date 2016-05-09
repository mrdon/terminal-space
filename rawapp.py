import sys

from colorclass import Color
from pytw.config import GameConfig
from pytw.server import Server
from pytw_ansi.session import Session
from pytw_ansi.stream import Terminal


class TestApp:
    def __init__(self):
        self.config = GameConfig(1, "Test Game", diameter=10, seed="test", debug_network=True)
        self.server = Server(self.config)

    def run(self):
        def cb(text):
            sys.stdout.write(Color("{hiblue}OUT: {blue}{text}{/blue}").format(text=text))
            sys.stdout.write('\n')
            sys.stdout.flush()

        in_cb = self.server.join("Bob", cb)
        while True:
            line = sys.stdin.readline().strip()
            if line:
                in_cb(line)
            else:
                break


if __name__ == '__main__':
    TestApp().run()
