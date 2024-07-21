import asyncio
from asyncio import Future
from functools import partial

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, Window, to_container
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Label

from tspace.client.logging import log
from tspace.client.scene.base import Scene
from tspace.client.ui.menu import MenuDialog
from tspace.client.ui.starfield import Starfield


class TitleScene(Scene):
    def __init__(self):
        self.starfield = Starfield()
        self.dialog = MenuDialog(
            title="Terminal Space",
            body=Label(
                text="   A text-based\n space trading game",
                dont_extend_width=False,
                width=20,
                dont_extend_height=True,
            ),
            buttons=[
                Button(text="New Game", handler=self.on_new_game),
                Button(text="Join Game", handler=partial(self.do_exit, "join")),
                Button(text="Quit", handler=partial(self.do_exit, "quit")),
            ],
            background=self.starfield,
            on_dismiss=partial(self.do_exit, "quit"),
        )

        self.layout = Layout(self.dialog)
        self.future = Future()

    def on_new_game(self):
        self.layout.container = self.starfield.window

        async def speed_up():
            for _ in range(4):
                self.starfield.speed *= 2.5
                await asyncio.sleep(0.5)

        task = asyncio.create_task(speed_up())
        task.add_done_callback(lambda _: self.do_exit("start"))

    def do_exit(self, result, *_):
        self.starfield.paused = True
        self.future.set_result(result)

    async def start(self):
        log.info("Starting title")
        self.starfield.reset_speed()
        self.layout.container = to_container(self.dialog)
        result = await self.future
        self.future = Future()
        return result

    def end(self):
        self.starfield.paused = True
        pass

    async def run(self):
        cmd = await self.start()
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
        pass
