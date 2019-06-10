import cmd
from sys import stdout
from typing import Callable

from colorclass import Color
from pytw.moves import TraderShipPublic
from pytw.util import methods_to_json
from pytw_ansi.instant_cmd import InstantCmd, InvalidSelectionError
from pytw_ansi.models import *
from pytw_ansi.prompts import PromptType, PromptTransition
from pytw_ansi.stream import Terminal, print_grid, print_action
from termcolor import colored


@methods_to_json()
class Actions:
    def __init__(self, server: Callable[[str], None]):
        self.target = server

    def move_trader(self, sector_id: int):
        pass


# noinspection PyMethodMayBeStatic,PyIncorrectDocstring
class Prompt:
    def __init__(self, player: PlayerClient, actions: Actions, term: Terminal):
        self.out = term
        self.player = player
        self.actions = actions

        self.instant_cmd = InstantCmd()
        self.instant_cmd.literal('d', default=True)(self.do_d)
        self.instant_cmd.literal('p')(self.do_p)
        self.instant_cmd.literal('q')(self.do_q)
        self.instant_cmd.regex('[0-9]+', max_length=4)(self.do_move)

    # noinspection PyUnusedLocal
    def do_d(self, line):
        """
        Re-display the current sector
        """
        print_action(self.out, 'Redisplay')
        self.print_sector()

    def do_p(self, line):
        raise PromptTransition(PromptType.PORT)

    def do_q(self, line):
        raise PromptTransition(PromptType.QUIT)

    def cmdloop(self):
        while True:
            try:
                self.out.write(self.prompt)
                return self.instant_cmd.cmdloop()
            except InvalidSelectionError:
                self.out.nl()

    @property
    def prompt(self):
        s = self.player.ship.sector
        return colored('Command [', 'magenta') + \
               colored('TL', color='yellow') + \
               colored('=', color='magenta') + \
               colored('00:00:00', color='yellow') + \
               colored(']', color='magenta') + \
               colored(':', color='yellow') + \
               colored('[', color='magenta') + \
               colored(s.id, color='cyan') + \
               colored('] (', color='magenta') + \
               colored('?=Help', color='yellow') + \
               colored(')? : ', color='magenta')

    def do_move(self, target_sector):
        """
        Move to an adjacent sector
        """
        try:
            target_id = int(target_sector)
        except ValueError:
            self.out.error("Invalid sector number")
            return
        print_action(self.out, "Move")
        self.out.write(Color("{magenta}Warping to Sector {/magenta}{yellow}{}{/yellow}").format(target_id))
        self.out.nl(2)
        self.actions.move_trader(sector_id=target_id)

    def print_sector(self, sector: SectorClient = None):

        if not sector:
            sector = self.player.ship.sector

        data = [(colored('Sector', 'green', attrs=['bold']), [
            "{} {} {}".format(
                    colored(sector.id, 'cyan'),
                    colored('in', 'green'),
                    colored('uncharted space', 'blue'))
        ])]
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
                "".join([colored(p.name, 'cyan'),
                         colored(", ", 'yellow'),
                         colored('Class ', 'magenta'),
                         colored(p.class_number, 'cyan'),
                         colored(' (', 'magenta'),
                         p.class_name_colored,
                         colored(')', 'magenta')])

            ]))

        if sector.ships:
            lines = []
            for ship in [s for s in sector.ships if s.trader.id != self.player.ship.id]:
                lines.append(Color("{red}{trader}{/red}{yellow},{/yellow}").format(trader=ship.trader.name))
                lines.append(Color("{green}in{/green} {cyan}{ship}{/cyan} {green}({ship_type}){/green}").format(
                        ship=ship.name,
                        ship_type="unknown"
                ))
            data.append((Color.yellow("Ships"), lines))

        print_grid(self.out, data, separator=colored(': ', 'yellow'))

        warps = []
        for w in sector.warps:
            if w in self.player.visited:
                warps.append(colored(w, 'cyan'))
            else:
                warps.append(colored('(', 'magenta') +
                             colored(w, 'red') +
                             colored(')', 'magenta'))

        data = [(colored("Warps to Sector(s)", 'green', attrs=['bold']), [colored(" - ", 'green').join(warps)])]
        print_grid(self.out, data, separator=colored(': ', 'yellow'))
        self.out.nl()

    def print_ship_enter_sector(self, ship):
        self.out.nl()
        self.out.write(Color("{b}{cyan}{trader}{/cyan}{/b} {green}warps into the sector.{/green}")
                       .format(trader=ship.trader.name))
        self.out.nl()

    def print_ship_exit_sector(self, ship):
        self.out.nl()
        self.out.write(Color("{b}{cyan}{trader}{/cyan}{/b} {green}warps out of the sector.{/green}")
                       .format(trader=ship.trader.name))
        self.out.nl()


class Events:
    def __init__(self, prompt: Prompt):
        self.prompt = prompt

    def on_game_enter(self, player: PlayerClient):
        self.prompt.player = player
        self.prompt.print_sector()

    def on_new_sector(self, sector: SectorClient):
        self.prompt.player.ship.sector = sector
        self.prompt.player.visited.add(sector.id)
        self.prompt.print_sector()

    def on_ship_enter_sector(self, sector: SectorClient, ship: TraderShipClient):
        self.prompt.player.ship.sector = sector
        if self.prompt.player.ship.sector.id == sector.id:
            self.prompt.print_ship_enter_sector(ship)

    def on_ship_exit_sector(self, sector: SectorClient, ship: TraderShipClient):
        self.prompt.player.ship.sector = sector
        if self.prompt.player.ship.sector.id == sector.id:
            self.prompt.print_ship_exit_sector(ship)

    # noinspection PyMethodMayBeStatic
    def on_invalid_action(self, error: str):
        self.prompt.out.error(error)
