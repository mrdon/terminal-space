import cmd
from typing import Callable

from colorclass import Color
from pytw.util import methods_to_json
from pytw_ansi.models import *
from pytw_ansi.prompts import PromptTransition, PromptType
from pytw_ansi.stream import Terminal, print_action, print_menu, amount_prompt, yesno_prompt
from tabulate import tabulate, TableFormat, Line, DataRow


@methods_to_json()
class Actions:
    def __init__(self, server: Callable[[str], None]):
        self.target = server

    def buy_from_port(self, commodity: CommodityType, amount: int):
        pass

    def sell_to_port(self, commodity: CommodityType, amount: int):
        pass


class Prompt(cmd.Cmd):
    def __init__(self, player: PlayerClient, actions: Actions, term: Terminal):
        super().__init__(stdout=term.out, stdin=term.stdin)
        self.out = term
        self.use_rawinput = False
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
        self._print_table(self.player.ship, self.player.ship.sector.port)
        raise PromptTransition(PromptType.SECTOR)

    def _print_table(self, ship: ShipClient, port: PortClient):
        print_action(self.out, "Port")
        self.out.print("Docking...", color='red', attrs=['blink'])
        self.out.write(Color("""

{hiyellow}Commerce report for {hicyan}{port_name}{hiyellow}: 12:50:33 PM Sat May 06, 2028

{magenta}-=-=-        Docking Log        -=-=-

{green}No current ship docking log on file.

""").format(port_name=port.name))
        rows = []
        for c in port.commodities:
            rows.append([Color("{hicyan}{name}").format(name=c.type.value),
                         Color.green("Buying" if c.buying else "Selling"),
                         Color("{hicyan}{}").format(c.amount),
                         Color("{green}{}{red}%").format(int(c.amount / c.capacity * 100)),
                         Color.cyan(ship.holds[c.type])])

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

        self.print_trader_status()

        if self.player.ship.holds_free < self.player.ship.holds_capacity:
            for c in port.commodities:
                in_holds = self.player.ship.holds.get(c.type, 0)
                if c.buying and c.amount and in_holds:
                    amount = min(c.amount, in_holds)
                    self.out.write(Color("{magenta}We are buying up to {hiyellow}{available}{magenta}.  "
                                         "You have {hiyellow}{existing} {magenta}in your holds. ")
                                   .format(available=c.amount, existing=self.player.ship.holds[c.type]))
                    self.out.nl()
                    value = amount_prompt(
                            stream=self.out,
                            prompt="{magenta}How many holds of {hicyan}{type} {magenta}do you want to sell",
                            default=amount,
                            min=0,
                            max=amount,
                            type=c.type.value)
                    if value:
                        self.out.write(Color("{hicyan}Agreed, {hiyellow}{} {hicyan} units.").format(value))
                        self.out.nl(2)
                        if yesno_prompt(self.out,
                                        prompt="{green}We'll buy them for {hiyellow}{price} {green}credits.",
                                        default=True,
                                        price=int(c.price * value)):
                            self.actions.sell_to_port(commodity=c.type, amount=amount)

                            self.out.write(Color.magenta("You drive a hard bargain, but we'll take them."))
                            self.out.nl(2)

        if self.player.ship.holds_free and sum([c.amount for c in port.commodities if not c.buying]):
            for c in port.commodities:
                amount = min(self.player.ship.holds_free, c.amount)
                if not c.buying and amount:
                    existing = self.player.ship.holds.get(c.type, 0)

                    self.out.write(Color("{magenta}We are selling up to {hiyellow}{available}{magenta}.  "
                                         "You have {hiyellow}{existing} {magenta}in your holds. ")
                                   .format(available=c.amount, existing=existing))
                    self.out.nl()
                    value = amount_prompt(
                            stream=self.out,
                            prompt="{magenta}How many holds of {hicyan}{type} {magenta}do you want to buy",
                            default=amount,
                            min=0,
                            max=amount,
                            type=c.type.value)
                    if value:
                        self.out.write(Color("{hicyan}Agreed, {hiyellow}{} {hicyan} units.").format(value))
                        self.out.nl(2)
                        if yesno_prompt(self.out,
                                        prompt="{green}We'll sell them for {hiyellow}{price} {green}credits.",
                                        default=True,
                                        price=int(c.price * value)):
                            self.actions.buy_from_port(commodity=c.type, amount=amount)

                            self.out.write(Color.green("You are a shrewd trader, they're all yours."))
                            self.out.nl(2)

                    self.print_trader_status()

                    # self.out.print(" Items     Status  Trading % of max OnBoard", 'green')
                    # self.out.nl()
                    # self.out.print(" -----     ------  ------- -------- -------", 'magenta')
                    # for c in port.commodities:
                    #     self.out.print(c.type.replace('_', ' ').title(), 'cyan', attrs=['bold'])
                    #     self.out.write(" " * (12 - len(c.type)))
                    #     self.out.print("Buying" if c.buying else "Selling")
                    #     self.out.write(" " * (26 - ))

    def print_trader_status(self):
        self.out.write(Color("{green}You have {hiyellow}{credits} {green}credits and "
                             "{hiyellow}{holds}{green} empty cargo holds").format(
                credits=self.player.credits,
                holds=self.player.ship.holds_free
        ))
        self.out.nl(2)


class Events:
    def __init__(self, prompt: Prompt):
        self.prompt = prompt

    # noinspection PyMethodMayBeStatic
    def on_invalid_action(self, error: str):
        self.prompt.out.error(error)

    def on_port_buy(self, id: int, player: PlayerClient):
        self.prompt.player.update(player)
        # todo: when async, make this sync on event id

    def on_port_sell(self, id: int, player: PlayerClient):
        self.prompt.player.update(player)
        # todo: when async, make this sync on event id
