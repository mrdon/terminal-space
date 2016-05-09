from aiohttp.web import Application, run_app
from pytw_ansi.web import websocket_handler

app = Application()
app.router.add_route('GET', '/', websocket_handler)
app.router.add_static("/public", 'public')
run_app(app)
