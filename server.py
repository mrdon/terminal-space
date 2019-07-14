from aiohttp.web import Application, run_app

from pytw.web import WebGame

webgame = WebGame()
app = Application()
app.router.add_route('GET', '/', webgame.handler)
run_app(app)
