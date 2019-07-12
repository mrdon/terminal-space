import asyncio
from asyncio import CancelledError
from asyncio import Queue

import aiohttp

from pytw_textui.full_screen import TwApplication


async def run():
    app = TwApplication()
    await app.start()


if __name__ == "__main__":
    # faulthandler.dump_traceback_later(3, exit=True)
    asyncio.get_event_loop().run_until_complete(run())
    print("end?")
