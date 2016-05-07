import cmd
from typing import Callable

from colorclass import Color
from pytw.util import methods_to_json
from pytw_ansi.models import *
from pytw_ansi.prompts import PromptTransition, PromptType
from pytw_ansi.stream import TerminalOutput, print_grid, print_action, print_menu
from tabulate import tabulate, TableFormat, Line, DataRow
from termcolor import colored


@methods_to_json()
class Actions:
    def __init__(self, server: Callable[[str], None]):
        self.target = server


class Prompt(cmd.Cmd):
    def __init__(self, player: PlayerClient, actions: Actions, stdin, stdout: TerminalOutput):
        super().__init__(stdout=stdout, stdin=stdin)
        self.out = stdout
        self.player = player
        self.actions = actions

        self.out.nl()
        self.prompt = print_menu(self.out, "T", (("T", "Trade at this Port"), ("Q", "Quit, nevermind")))

    def emptyline(self):
        self.do_t('')

    def do_q(self, line):
        """
        Go back to the sector prompt
        """
        self.out.nl()
        raise PromptTransition(PromptType.SECTOR)

    def do_t(self, line):
        self._print_table(self.player.ship.sector.port)
        raise PromptTransition(PromptType.SECTOR)

    def _print_table(self, port: PortClient):
        print_action(self.out, "Port")
        self.out.print("Docking...", color='red', attrs=['blink'])
        self.out.write(Color("""

{hiyellow}Commerce report for {hicyan}{port_name}{hiyellow}: 12:50:33 PM Sat May 06, 2028{/hiyellow}

{magenta}-=-=-        Docking Log        -=-=-{/magenta}

{green}No current ship docking log on file.{/green}

""").format(port_name=port.name))
        rows = []
        for c in port.commodities:
            rows.append([Color("{hicyan}{name}{/hicyan}").format(name=c.type.name.replace('_', ' ').title()),
                         Color.green("Buying" if c.buying else "Selling"),
                         Color("{hicyan}{}{/hicyan}").format(c.amount),
                         Color("{green}{}{red}%{/red}").format(int(c.amount / c.capacity)),
                         Color.cyan('0')])

        self.out.write(tabulate(
                tabular_data=rows,
                stralign="center",
                numalign="center",
                headers=(Color.green(t) for t in ["Items", "Status", "Trading", "% of max", "OnBoard"]),
                tablefmt=TableFormat(lineabove=Line("", "-", "  ", ""),
                                     linebelowheader=Line("", Color.magenta("-"), "  ", ""),
                                     linebetweenrows=None,
                                     linebelow=Line("", "-", "  ", ""),
                                     headerrow=DataRow("", "  ", ""),
                                     datarow=DataRow("", "  ", ""),
                                     padding=0,
                                     with_header_hide=["lineabove", "linebelow"])))
        self.out.nl(2)


        # self.out.print(" Items     Status  Trading % of max OnBoard", 'green')
        # self.out.nl()
        # self.out.print(" -----     ------  ------- -------- -------", 'magenta')
        # for c in port.commodities:
        #     self.out.print(c.type.replace('_', ' ').title(), 'cyan', attrs=['bold'])
        #     self.out.write(" " * (12 - len(c.type)))
        #     self.out.print("Buying" if c.buying else "Selling")
        #     self.out.write(" " * (26 - ))


class Events:
    def __init__(self, prompt: Prompt):
        self.prompt = prompt

    # noinspection PyMethodMayBeStatic
    def on_invalid_action(self, error: str):
        self.prompt.out.error(error)
