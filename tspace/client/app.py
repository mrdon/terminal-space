import asyncio
from asyncio import CancelledError
from asyncio import Queue

import aiohttp
from prompt_toolkit import Application
from prompt_toolkit.data_structures import Size
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.styles import Style

from tspace.client.logging import log
from tspace.client.scene.base import Scene, SceneId
from tspace.client.scene.game import TerminalScene
from tspace.client.scene.main_menu import TitleScene
from tspace.client.ui import style
from tspace.client.util import sync_to_async
from tspace.common.background import schedule_background_task
from tspace.server.config import GameConfig
from tspace.server.server import Server


class InvalidScreenSize(Exception):
    def __init__(self, expected: Size, actual: Size):
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return f"Invalid screen size: expected {self.expected} but was {self.actual}"


class TwApplication(Application):
    def __init__(self, local: bool = False):
        super().__init__(
            mouse_support=True,
            full_screen=True,
            refresh_interval=1 / 15,
            style=style.css,
            color_depth=ColorDepth.DEPTH_8_BIT,
        )

        self._local_mode = local
        self.title_scene = TitleScene(self)
        self.scene: Scene = self.title_scene
        self.layout = self.title_scene.layout
        self.fps = 15

        actual: Size = self.output.get_size()
        expected = Size(rows=40, columns=120)
        if actual.rows < expected.rows or actual.columns < expected.columns:
            raise InvalidScreenSize(expected, actual)

    async def start(self):
        ui_task = asyncio.create_task(self.run_async())


        if self._local_mode:
            game_scene = TerminalScene(self, lambda x: None)
            self.scene = game_scene

        while True:
            self.layout = self.scene.layout
            self.invalidate()
            scene_id = await self.scene.run()
            match scene_id:
                case SceneId.MAIN_MENU:
                    self.scene = self.title_scene
                case SceneId.GAME:
                    self.scene = game_scene
                case SceneId.QUIT:
                    self.exit()
                    await ui_task
                    break
                case _:
                    breakpoint()

            action = await self.scene.start()
            log.info(f"got {action} from title")
            if action == "start":
                await self.start_game()
            elif action == "join":
                await self.join("localhost", "8080")
            elif action == "quit":
                self.exit()
                await ui_task
                break
            else:
                breakpoint()


        if self._local_mode:
            await self.start_game()
            self.exit()
            await ui_task
            return

        while True:
            self.layout = self.title_scene.layout
            self.invalidate()
            action = await self.title_scene.start()
            log.info(f"got {action} from title")
            if action == "start":
                await self.start_game()
            elif action == "join":
                await self.join("localhost", "8080")
            elif action == "quit":
                self.exit()
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
            async with aiosession.ws_connect(
                f"ws://{host}:{port}/?name=Remote%20Jim"
            ) as ws:

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
                schedule_background_task(read_input())

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

        incoming_for_server = await server.join(
            "Jim", sync_to_async(server_to_app.put_nowait)
        )

        terminal_scene = TerminalScene(self, incoming_for_server)
        self.layout = terminal_scene.layout

        async def read_from_server():
            while True:
                msg = await server_to_app.get()
                log.info(f"got server-to_app: {msg}")
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
