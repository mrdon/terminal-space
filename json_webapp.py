from aiohttp.web import Application, run_app

from pytw.web import WebGame
from pytw_ansi.web import websocket_handler

webgame = WebGame()
app = Application()
app.router.add_route('GET', '/', webgame.handler)
app.router.add_static("/public", 'public')
run_app(app)
