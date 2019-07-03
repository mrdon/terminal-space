import asyncio
from asyncio import CancelledError
from asyncio import Queue

import aiohttp

from pytw_textui.full_screen import TwApplication


async def run():
    in_queue = Queue()
    out_queue = Queue()
    app = TwApplication(in_queue, out_queue)

    async with aiohttp.ClientSession() as aiosession:
        async with aiosession.ws_connect('ws://localhost:8080/') as ws:

            async def read_input():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        in_queue.put_nowait(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print("error")
                        break

            async def send_output():
                while True:
                    text = await out_queue.get()
                    await ws.send_str(text)

            asyncio.create_task(send_output())
            asyncio.create_task(read_input())
            try:
                await app.start()
            except CancelledError:
                print("cancelled'")

                pass


if __name__ == "__main__":
    # faulthandler.dump_traceback_later(3, exit=True)
    asyncio.get_event_loop().run_until_complete(run())
    print("end?")
