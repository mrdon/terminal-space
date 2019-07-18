import asyncio
from asyncio import CancelledError
from asyncio import Queue

import aiohttp
from prompt_toolkit import Application
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.styles import Style

from tspace.server.config import GameConfig
from tspace.server.server import Server
from tspace.client.scene.game import TerminalScene
from tspace.client.scene.main_menu import TitleScene


class InvalidScreenSize(Exception):
    def __init__(self, expected: Size, actual: Size):
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return f"Invalid screen size: expected {self.expected} but was {self.actual}"


class TwApplication(Application):
    def __init__(self):
        super().__init__(
            mouse_support=True,
            full_screen=True,
            style=Style([("dialog", "bg:#fff333")]),
        )

        self.title_scene = TitleScene(self)
        self.layout = self.title_scene.layout

        actual: Size = self.output.get_size()
        expected = Size(rows=40, columns=120)
        if actual.rows < expected.rows or actual.columns < expected.columns:
            raise InvalidScreenSize(expected, actual)

    async def start(self):
        use_asyncio_event_loop()
        ui_task = self.run_async().to_asyncio_future()

        while True:
            self.layout = self.title_scene.layout
            self.invalidate()
            action = await self.title_scene.start()
            if action == "start":
                await self.start_game()
            elif action == "join":
                await self.join("localhost", "8080")
            elif action == "quit":
                self.exit(False)
                await ui_task
                break
            else:
                breakpoint()

            # self.exit(False)
        # await ui_task

    async def join(self, host: str, port: str):

        out_queue = Queue()

        terminal_scene = TerminalScene(self, lambda text: out_queue.put(text))
        self.layout = terminal_scene.layout

        async with aiohttp.ClientSession() as aiosession:
            async with aiosession.ws_connect(f"ws://{host}:{port}/") as ws:

                async def read_input():
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await terminal_scene.session.bus(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print("error")
                            break

                async def write_output():
                    while True:
                        try:
                            msg = await out_queue.get()
                        except InterruptedError:
                            break
                        await ws.send_str(msg)

                write_task = asyncio.create_task(write_output())
                asyncio.create_task(read_input())

                try:
                    await terminal_scene.start()
                except CancelledError:
                    pass  # print("cancelled'")

                write_task.cancel()

        terminal_scene.end()

    async def start_game(self):
        config = GameConfig(
            1, "Test Game", diameter=10, seed="test", debug_network=False
        )
        server = Server(config)

        server_to_app = Queue()

        in_cb = await server.join("Bob", lambda text: asyncio.coroutine(server_to_app.put_nowait)(text))

        terminal_scene = TerminalScene(self, in_cb)
        self.layout = terminal_scene.layout

        async def read_from_server():
            while True:
                msg = await server_to_app.get()
                await terminal_scene.session.bus(msg)

        server_out_task = asyncio.create_task(read_from_server())

        try:
            await terminal_scene.start()
        except CancelledError:
            pass  # print("cancelled'")

        server_out_task.cancel()

        terminal_scene.end()

if __name__ == "__main__":
    async def run():
        app = TwApplication()
        await app.start()

    asyncio.get_event_loop().run_until_complete(run())
