import asyncio

from tspace.client.app import TwApplication


async def run():
    app = TwApplication()
    await app.start()


def main():
    asyncio.get_event_loop().run_until_complete(run())


if __name__ == "__main__":
    main()
