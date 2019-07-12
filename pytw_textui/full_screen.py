import asyncio
from asyncio import CancelledError

import aiohttp
from prompt_toolkit import Application
from prompt_toolkit.eventloop import use_asyncio_event_loop

from pytw_textui.session import Session
from pytw_textui.stream import Terminal
from pytw_textui.terminal_scene import TerminalScene


class TwApplication(Application):
    def __init__(self):
        super().__init__(
            mouse_support=True,
            full_screen=True)

    async def start(self):
        use_asyncio_event_loop()
        ui_task = self.run_async().to_asyncio_future()
    
        try:
            await self.join("localhost", "8080")
        finally:
            self.exit(False)
        await ui_task

    async def join(self, host: str, port: str):

        terminal_scene = TerminalScene(self)
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

                asyncio.create_task(read_input())

                try:
                    await terminal_scene.session.start(lambda text: ws.send_str(text))
                except CancelledError:
                    print("cancelled'")