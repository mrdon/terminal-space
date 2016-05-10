import threading
from queue import Queue

import aiohttp
from aiohttp import web
from colorclass.codes import ANSICodeMapping
from pytw.config import GameConfig
from pytw.server import Server
from pytw_ansi.session import Session
from pytw_ansi.stream import Terminal


class WsWriter:
    def __init__(self, ws: web.WebSocketResponse):
        self.ws = ws

    def write(self, data):
        self.ws.send_str(data)

    def flush(self):
        pass


class WsReader:
    def __init__(self):
        self._queue = Queue()

    def write(self, line):
        self._queue.put(line)

    def read(self, chars):
        while True:
            buffer = []
            while len(buffer) < chars:
                item = self._queue.get()
                buffer.append(item)
            self._queue.task_done()
            return "".join(buffer)

    def readline(self):
        while True:
            buffer = []
            while True:
                item = self._queue.get()
                buffer.append(item)
                if item == '\n':
                    result = "".join(buffer)
                    self._queue.task_done()
                    return result


async def websocket_handler(request):

    config = GameConfig(1, "Test Game", diameter=10, seed="test", debug_network=True)
    server = Server(config)

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    stdin = WsReader()
    ANSICodeMapping.enable_all_colors()
    out = Terminal(out=WsWriter(ws), input=stdin)
    session = Session(config, out, server)
    t = threading.Thread(target=session.start)
    t.start()
    async for msg in ws:
        if msg.tp == aiohttp.MsgType.text:
            stdin.write(msg.data)
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws