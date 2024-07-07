import argparse
import asyncio
from tspace.client.app import TwApplication
from tspace.client.logging import log


parser = argparse.ArgumentParser(prog="terminal-space")
parser.add_argument("--local", action="store_true", help="Skip straight to local game")


async def run():
    log.info("Starting terminal space")
    args = parser.parse_args()
    app = TwApplication(local=args.local)
    await app.start()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
