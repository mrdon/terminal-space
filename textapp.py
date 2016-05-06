import cmd
import enum
import re
import sys
from functools import partial
from typing import Set, List, Tuple, Callable

from pytw.server import Server
from pytw.util import methods_to_json, call_type
from termcolor import colored


class ConsoleOutput:
    def __init__(self):
        self.out = sys.stdout

    def write(self, text):
        self.out.write(text)

    def print(self, text, color=None, on_color=None, attrs=None):
        self.out.write(colored(text, color=color, on_color=on_color, attrs=attrs))

    def nl(self):
        self.out.write('\n')

    def error(self, msg):
        self.nl()
        self.print(msg, 'red')
        self.nl()
        self.nl()


class TestApp:
    def __init__(self):
        self.server = Server(seed="test")
        self.out = ConsoleOutput()
        self.game = GameProcessor(sys.stdin, self.out)
        events = ClientEvents(self.game)

        self.target = self.server.join("Bob", partial(call_type, events))
        actions = ClientActions(self.game, self.target)
        self.game.actions = actions

    def run(self):
        self.out.print("Welcome to PyTW!", 'red', attrs=['bold'])

        self.game.cmdloop()


class TradingCommodityClient:
    def __init__(self, type: str, buying: bool, amount: int, capacity: int):
        self.capacity = capacity
        self.amount = amount
        self.buying = buying
        self.type = CommodityType[type]


class CommodityType(enum.Enum):
    fuel_ore = 1,
    organics = 2,
    equipment = 3


class PortClient:

    CLASSES = {
        "BBS": 1,
        "BSB": 2,
        "SBB": 3,
        "SSB": 4,
        "SBS": 5,
        "BSS": 6,
        "SSS": 7,
        "BBB": 8
    }

    def __init__(self, sector_id: int, name: str, commodities: List[TradingCommodityClient]):
        self.commodities = commodities
        self.name = name
        self.sector_id = sector_id

    @property
    def class_name(self):
        c = {c.type: c.buying for c in self.commodities}

        name = []
        for ctype in CommodityType:
            name.append("B" if c[ctype] else "S")

        return "".join(name)

    @property
    def class_name_colored(self):
        line = []
        for c in self.class_name:
            line.append(colored(c, 'cyan', attrs=['bold']) if c == 'B' else colored(c, 'green'))
        return "".join(line)

    @property
    def class_number(self):
        return self.CLASSES[self.class_name]


class SectorClient:
    def __init__(self, id: int, coords: Tuple[int, int], warps: List[int], port: PortClient):
        self.port = port
        self.warps = warps
        self.coords = coords
        self.id = id
        self.traders = None  # todo
        self.ships = None  # todo


class ShipClient:
    def __init__(self, id: int, name: str, sector: SectorClient):
        self.sector = sector
        self.name = name
        self.id = id


class PlayerClient:

    def __init__(self, id: int, name: str, ship: ShipClient, visited: Set[int]):
        self.visited = visited
        self.ship = ship
        self.name = name
        self.id = id


class GameProcessor(cmd.Cmd):

    actions = None  # type: ClientActions
    player = None  # type: PlayerClient

    def __init__(self, stdin, stdout: ConsoleOutput):
        super().__init__(stdout=stdout, stdin=stdin)
        self.out = stdout

    def do_d(self, line):
        self._print_action('Redisplay')
        self.print_sector()

    def emptyline(self):
        self.do_d('')

    def default(self, line):
        self.do_move(line)

    def _print_action(self, title):
        self.out.nl()
        self.out.print("<{}>".format(title), 'white', on_color='on_blue', attrs=['bold'])
        self.out.nl()

    @property
    def prompt(self):
        sector = self.player.ship.sector
        return colored('Command [', 'magenta') + \
                colored('TL', color='yellow', attrs=['bold']) + \
                colored('=', color='magenta') + \
                colored('00:00:00', color='yellow', attrs=['bold']) + \
                colored(']', color='magenta') + \
                colored(':', color='yellow') + \
                colored('[', color='magenta') + \
                colored(sector.id, color='cyan', attrs=['bold']) + \
                colored('] (', color='magenta') + \
                colored('?=Help', color='yellow', attrs=['bold']) + \
                colored(')? : ', color='magenta')

    def do_move(self, target_sector):
        try:
            target_id = int(target_sector)
        except ValueError:
            self.out.error("Invalid sector number")
            return
        self._print_action("Moving to sector {}".format(target_id))
        self.actions.move_trader(sector_id=target_id)

    def print_sector(self, sector: SectorClient = None):
        if not sector:
            sector = self.player.ship.sector

        data = []
        data.append((colored('Sector', 'green', attrs=['bold']), [
            "{} {} {}".format(
                colored(sector.id, 'cyan', attrs=['bold']),
                colored('in', 'green'),
                colored('uncharted space', 'blue'))
        ]))
        # if sector.planets:
        #     lines = []
        #     for planet in sector.planets:
        #         lines.append(colored("({}) {}".format(
        #             colored('M', color='yellow', attrs=['bold']),
        #             planet.name)
        #         ))
        #     data.append((colored('Planets', 'magenta'), lines))

        if sector.port:
            p = sector.port
            data.append((colored('Port', 'magenta'), [
                "".join([colored(p.name, 'cyan', attrs=['bold']),
                         colored(", ", 'yellow'),
                         colored('Class ', 'magenta'),
                         colored(p.class_number, 'cyan', attrs=['bold']),
                         colored(' (', 'magenta'),
                         p.class_name_colored,
                         colored(')', 'magenta')])


            ]))

        print_grid(self.out, data, separator=colored(': ', 'yellow'))

        warps = []
        for w in sector.warps:
            if w in self.player.visited:
                warps.append(colored(w, 'cyan', attrs=['bold']))
            else:
                warps.append(colored('(', 'magenta') +
                             colored(w, 'red') +
                             colored(')', 'magenta'))

        data = [(colored("Warps to Sector(s)", 'green', attrs=['bold']), [colored(" - ", 'green').join(warps)])]
        print_grid(self.out, data, separator=colored(': ', 'yellow'))
        self.out.nl()

    def do_EOF(self, line):
        return True


class ClientEvents:
    def __init__(self, game: GameProcessor):
        self.game = game

    def on_game_enter(self, player: PlayerClient):
        self.game.player = player
        self.game.print_sector()

    def on_new_sector(self, sector: SectorClient):
        self.game.player.ship.sector = sector
        self.game.player.visited.add(sector.id)
        self.game.print_sector()

    # noinspection PyMethodMayBeStatic
    def on_invalid_action(self, error: str):
        self.game.out.error(error)


@methods_to_json()
class ClientActions:
    def __init__(self, game: GameProcessor, server: Callable[[str], None]):
        self.game = game
        self.target = server

    def move_trader(self, sector_id: int):
        pass


def print_grid(stream, data, separator):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    header_len = max(len(ansi_escape.sub('', h[0])) for h in data) + 1
    for header, row in data:
        text = ansi_escape.sub('', header)
        stream.write(header)
        stream.write(' ' * (header_len - len(text)))
        stream.write(separator)
        pad = False
        for line in row:
            if pad:
                stream.write(" " * (header_len + 2))
            else:
                pad = True
            stream.write(line)
            stream.write('\n')


if __name__ == '__main__':
    TestApp().run()
