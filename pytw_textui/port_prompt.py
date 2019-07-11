import cmd
from typing import Awaitable
from typing import Callable

from colorclass import Color
from pytw.util import methods_to_json
from pytw_textui.models import *
from pytw_textui.prompts import PromptTransition, PromptType
from pytw_textui.stream import Terminal, print_action, amount_prompt, yesno_prompt, \
    SimpleMenuCmd
from tabulate import tabulate, TableFormat, Line, DataRow


@methods_to_json()
class Actions:
    def __init__(self, server: Callable[[str], Awaitable[None]]):
        self.target = server

    async def buy_from_port(self, commodity: CommodityType, amount: int):
        pass

    async def sell_to_port(self, commodity: CommodityType, amount: int):
        pass

    async def exit_port(self, port_id: int):
        pass


class Prompt(SimpleMenuCmd):
    def __init__(self, player: Player, actions: Actions, term: Terminal):
        super().__init__(term, 'T', ('T', 'Q'))
        self.out = term
        self.player = player
        self.actions = actions
        self.out.nl()

    async def do_t(self, _):
        """
        Trade at this Port
        """
        await self._print_table(self.player.ship, self.player.ship.sector.port)
        raise PromptTransition(PromptType.SECTOR)

    async def do_q(self, _):
        """
        Quit, nevermind
        """
        self.out.nl(2)
        await self.actions.exit_port(port_id=self.player.port_id)
        raise PromptTransition(PromptType.NONE)

    async def _print_table(self, ship: Ship, port: Port):
        print_action(self.out, "Port")
        self.out.write_line(
            ('yellow', 'Commerce report for '),
            ('cyan', port.name),
            ('yellow', ': 12:50:33 PM Sat May 06, 2028')
        )
        self.out.nl()
        self.out.write_line(
            ('magenta', '-=-=-        Docking Log        -=-=-')
        )
        self.out.nl()
        self.out.write_line(
            ('green', 'No current ship docking log on file.')
        )
        rows = []
        for c in port.commodities.values():
            rows.append([Color.cyan("{name}").format(name=c.type.value),
                         Color.green("Buying" if c.buying else "Selling"),
                         Color.cyan("{}").format(c.amount),
                         Color("{green}{}{/green}{red}%{/red}").format(
                             int(c.amount / c.capacity * 100)),
                         Color.cyan(ship.holds[c.type])])

        self.out.write_ansi(tabulate(
            tabular_data=rows,
            stralign="center",
            numalign="center",
            headers=(Color.green(t) for t in
                     ["Items", "Status", "Trading", "% of max", "OnBoard"]),
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
                    self.out.write_line(
                        ('magenta', 'We are buying up to '),
                        ('yellow', str(c.amount)),
                        ('magenta', '. You have '),
                        ('yellow', str(self.player.ship.holds[c.type])),
                        ('magenta', 'in your holds. ')
                    )
                    self.out.nl()
                    value = amount_prompt(
                        stream=self.out,
                        prompt=(
                            ('magenta', 'How many holds of '),
                            ('cyan', c.type.value),
                            ('magenta', 'do you want to sell')
                        ),
                        default=amount,
                        min=0,
                        max=amount)
                    if value:
                        self.out.write_line(
                            ('cyan', 'Agreed, '),
                            ('yellow', str(value)),
                            ('cyan', ' units.'))
                        self.out.nl(2)
                        if await yesno_prompt(self.out,
                                        prompt=(
                                                ('green', "We'll buy them for "),
                                                ('yellow', str(int(c.price * value))),
                                                ('green', 'credits.')),
                                        default=True,
                                        price=int(c.price * value)):
                            await self.actions.sell_to_port(commodity=c.type, amount=value)

                            self.out.print("You drive a hard bargain, but we'll take them.", color='magenta')
                            self.out.nl(2)

        if self.player.ship.holds_free and sum(
                [c.amount for c in port.commodities.values() if not c.buying]):
            for c in port.commodities.values():
                amount = min(self.player.ship.holds_free, c.amount)
                if not c.buying and amount:
                    existing = self.player.ship.holds.get(c.type, 0)

                    self.out.write(Color(
                        "{magenta}We are selling up to {/magenta}{yellow}{available}{/yellow}"
                        "{magenta}. You have {/magenta}{yellow}{existing}{/yellow} "
                        "{magenta}in your holds.{/magenta}")
                                   .format(available=c.amount, existing=existing))
                    self.out.nl()
                    value = amount_prompt(
                        stream=self.out,
                        prompt="{magenta}How many holds of {/magenta}{cyan}{type}{/cyan} "
                               "{magenta}do you want to buy{/magenta}",
                        default=amount,
                        min=0,
                        max=amount,
                        type=c.type.value)
                    if value:
                        self.out.write(Color(
                            "{cyan}Agreed, {/cyan}{yellow}{} {/yellow}{cyan}units.{/cyan}")
                                       .format(value))
                        self.out.nl(2)
                        if yesno_prompt(self.out,
                                        prompt="{green}We'll sell them for {green}{yellow}{price}{/yellow} "
                                               "{green}credits.{/green}",
                                        default=True,
                                        price=int(c.price * value)):
                            self.actions.buy_from_port(commodity=c.type, amount=value)

                            self.out.write(Color.green(
                                "You are a shrewd trader, they're all yours."))
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
        self.out.write_line(
            ('green', 'You have '),
            ('yellow', str(self.player.credits)),
            ('green', ' credits and '),
            ('yellow', str(self.player.ship.holds_free)),
            ('green', ' empty cargo holds')
        )
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
