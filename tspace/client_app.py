import asyncio
from tspace.client.app import TwApplication
from tspace.client.logging import log


async def run():
    log.info("Starting terminal space")
    app = TwApplication()
    await app.start()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
