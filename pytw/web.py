import aiohttp
from aiohttp import web

from pytw.config import GameConfig
from pytw.server import Server


class WebGame:
    def __init__(self):
        self.config = GameConfig(
            1, "Test Game", diameter=10, seed="test", debug_network=False
        )
        self.server = Server(self.config)

    async def handler(self, request):
        print("websocket connected")
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async def cb(text):
            print(f"OUT: {text}")
            await ws.send_str(text)

        in_cb = await self.server.join("Bob", cb)

        print("server joined")
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.text:
                print("IN: %s" % msg.data)
                await in_cb(msg.data)
            elif msg.type == aiohttp.WSMsgType.error:
                print("ws connection closed with exception %s" % ws.exception())
            else:
                print("unexpected message type: %s" % msg.type)

        print("websocket connection closed")

        return ws
