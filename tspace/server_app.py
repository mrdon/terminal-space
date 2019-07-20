from aiohttp.web import Application, run_app

from tspace.server.web import WebGame


def main():
    webgame = WebGame()
    app = Application()
    app.router.add_route("GET", "/", webgame.handler)
    run_app(app)


if __name__ == "__main__":
    main()
