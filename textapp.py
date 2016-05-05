import textwrap

import sys

import re

from pytw.moves import ShipMoves
from pytw.planet import Galaxy
from termcolor import colored, cprint
import cmd


class TestApp:
    def __init__(self):
        self.game = Galaxy(1, "foo", 5)
        self.game.start()
        self.player = self.game.add_player("Bob")

    def run(self):
        cprint("Welcome to PyTW!", 'red', attrs=['bold'])

        GameProcessor(self.game, self.player).cmdloop()


class GameProcessor(cmd.Cmd):
    def __init__(self, game, player):
        super().__init__()
        self.game = game
        self.player = player
        self.moves = ShipMoves(self.player, self.game)

    def do_d(self, line):
        self._print_action('Redisplay')
        self.print_sector()

    def emptyline(self):
        self.do_d('')

    def default(self, line):
        self.do_move(line)

    def _print_action(self, title):
        print('')
        cprint("<{}>".format(title), 'white', on_color='on_blue', attrs=['bold'])
        print('')
    @property
    def prompt(self):
        sector = self.game.sectors[self.game.ships[self.player.current_ship_id].sector_id]
        return colored('Command [', 'magenta') + \
                colored('TL', color='yellow', attrs=['bold']) + \
                colored('=', color='magenta') + \
                colored('00:00:00', color='yellow', attrs=['bold']) + \
                colored(']', color='magenta') + \
                colored(':', color='yellow') + \
                colored('[', color='magenta') + \
                colored(sector.sector_id, color='cyan', attrs=['bold']) + \
                colored('] (', color='magenta') + \
                colored('?=Help', color='yellow', attrs=['bold']) + \
                colored(')? : ', color='magenta')

    def do_move(self, target_sector):
        self._print_action("Moving to sector {}".format(target_sector))
        try:
            self.moves.move_sector(self.player.current_ship_id, int(target_sector))
            self.print_sector()
        except ValueError as e:
            cprint(str(e), 'red')

    def print_sector(self):
        sector = self.game.sectors[self.game.ships[self.player.current_ship_id].sector_id]
        data = []
        data.append((colored('Sector', 'green', attrs=['bold']), [
            "{} {} {}".format(
                colored(sector.sector_id, 'cyan', attrs=['bold']),
                colored('in', 'green'),
                colored('uncharted space', 'blue'))
        ]))
        if sector.planets:
            lines = []
            for planet in sector.planets:
                lines.append(colored("({}) {}".format(
                    colored('M', color='yellow', attrs=['bold']),
                    planet.name)
                ))
            data.append((colored('Planets', 'magenta'), lines))

        print_grid(sys.stdout, data, separator=colored(': ', 'yellow'))

        warps = []
        for w in sector.warps:
            if self.player.has_visited(w):
                warps.append(colored(w, 'cyan', attrs=['bold']))
            else:
                warps.append(colored('(', 'magenta') +
                             colored(w, 'red') +
                             colored(')', 'magenta'))

        data = [(colored("Warps to Sector(s)", 'green', attrs=['bold']), [colored(" - ", 'green').join(warps)])]
        print_grid(sys.stdout, data, separator=colored(': ', 'yellow'))
        sys.stdout.write('\n')

    def do_EOF(self, line):
        return True


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
