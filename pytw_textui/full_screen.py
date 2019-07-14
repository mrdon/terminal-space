import asyncio
from asyncio import CancelledError
from asyncio import Queue

import aiohttp
from prompt_toolkit import Application
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.styles import Style

from pytw_textui.terminal_scene import TerminalScene
from pytw_textui.title_scene import TitleScene


class TwApplication(Application):
    def __init__(self):
        super().__init__(
            mouse_support=True,
            full_screen=True,
            style=Style([('dialog', 'bg:#fff333'),]))

        self.title_scene = TitleScene(self)
        self.layout = self.title_scene.layout

    async def start(self):
        use_asyncio_event_loop()
        ui_task = self.run_async().to_asyncio_future()

        while True:
            self.layout = self.title_scene.layout
            self.invalidate()
            action = await self.title_scene.start()
            if action == "start":
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
            async with aiosession.ws_connect(f'ws://{host}:{port}/') as ws:

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
                    pass # print("cancelled'")

                write_task.cancel()

        terminal_scene.end()