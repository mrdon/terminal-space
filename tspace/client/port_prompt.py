from typing import Tuple

from colorclass import Color
from tabulate import DataRow
from tabulate import Line
from tabulate import TableFormat
from tabulate import tabulate

from tspace.client.game import Game
from tspace.client.models import Port
from tspace.client.models import Ship
from tspace.client.prompts import PromptTransition
from tspace.client.prompts import PromptType
from tspace.client.stream import SimpleMenuCmd
from tspace.client.terminal import Terminal
from tspace.client.stream import amount_prompt
from tspace.client.stream import print_action
from tspace.client.stream import yesno_prompt
from tspace.common.models import PortPublic, PlayerPublic
from tspace.common.actions import PortActions
from tspace.common.events import ServerEvents


class Prompt(SimpleMenuCmd):
    def __init__(self, game: Game, actions: PortActions, term: Terminal):
        super().__init__(term, "T", ("T", "Q"))
        self.out = term
        self.game = game
        self.player = game.player
        self.actions = actions
        self.out.nl()

    async def do_t(self, _):
        """
        Trade at this Port
        """
        await self._print_table(self.player.ship, self.player.port)
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
            ("yellow", "Commerce report for "),
            ("cyan", port.name),
            ("yellow", ": 12:50:33 PM Sat May 06, 2028"),
        )
        self.out.nl()
        self.out.write_line(("magenta", "-=-=-        Docking Log        -=-=-"))
        self.out.nl(2)
        self.out.write_line(("green", "No current ship docking log on file."))
        self.out.nl(2)
        rows = []
        for c in port.commodities.values():
            rows.append(
                [
                    Color.cyan("{name}").format(name=c.type.value),
                    Color.green("Buying" if c.buying else "Selling"),
                    Color.cyan("{}").format(c.amount),
                    Color("{green}{}{/green}{red}%{/red}").format(
                        int(c.amount / c.capacity * 100)
                    ),
                    Color.cyan(str(ship.holds[c.type])),
                ]
            )

        self.out.write_ansi(
            tabulate(
                tabular_data=rows,
                stralign="center",
                numalign="center",
                headers=(
                    Color.green(t)
                    for t in ["Items", "Status", "Trading", "% of max", "OnBoard"]
                ),
                tablefmt=TableFormat(
                    lineabove=Line("", "-", "  ", ""),
                    linebelowheader=Line("", Color.magenta("-"), "  ", ""),
                    linebetweenrows=None,
                    linebelow=Line("", "-", "  ", ""),
                    headerrow=DataRow("", "  ", ""),
                    datarow=DataRow("", "  ", ""),
                    padding=0,
                    with_header_hide=["lineabove", "linebelow"],
                ),
            )
        )
        self.out.nl(2)

        self.print_trader_status()

        if self.player.ship.holds_free < self.player.ship.holds_capacity:
            for c in port.commodities.values():
                in_holds = self.player.ship.holds.get(c.type, 0)
                if c.buying and c.amount and in_holds:
                    amount = min(c.amount, in_holds)
                    self.out.write_line(
                        ("magenta", "We are buying up to "),
                        ("yellow", str(c.amount)),
                        ("magenta", ". You have "),
                        ("yellow", str(self.player.ship.holds[c.type])),
                        ("magenta", "in your holds. "),
                    )
                    self.out.nl()
                    value = await amount_prompt(
                        stream=self.out,
                        prompt=(
                            ("magenta", "How many holds of "),
                            ("cyan", c.type.value),
                            ("magenta", " do you want to sell"),
                        ),
                        default=amount,
                        min=0,
                        max=amount,
                    )
                    if value:
                        self.out.nl()
                        self.out.write_line(
                            ("cyan", "Agreed, "),
                            ("yellow", str(value)),
                            ("cyan", " units."),
                        )
                        self.out.nl(2)
                        if await yesno_prompt(
                            self.out,
                            prompt=(
                                ("green", "We'll buy them for "),
                                ("yellow", str(int(c.price * value))),
                                ("green", " credits."),
                            ),
                            default=True,
                        ):
                            player_client, port_client = (
                                await self.actions.sell_to_port(
                                    port_id=port.id, commodity=c.type, amount=value
                                )
                            )
                            self.game.update_player(player_client)
                            self.game.update_port(port_client)

                            self.out.nl()
                            self.out.print(
                                "You drive a hard bargain, but we'll take them.",
                                color="magenta",
                            )
                            self.out.nl(2)

        if self.player.ship.holds_free and sum(
            [c.amount for c in port.commodities.values() if not c.buying]
        ):
            for c in port.commodities.values():
                amount = min(self.player.ship.holds_free, c.amount)
                if not c.buying and amount:
                    existing = self.player.ship.holds.get(c.type, 0)

                    self.out.write_line(
                        ("magenta", "We are selling up to "),
                        ("yellow", str(c.amount)),
                        ("magenta", ". You have "),
                        ("yellow", str(existing)),
                        ("magenta", " in your holds."),
                    )
                    self.out.nl()
                    value = await amount_prompt(
                        stream=self.out,
                        prompt=[
                            ("magenta", "How many holds of "),
                            ("cyan", c.type.value),
                            ("magenta", " do you want to buy"),
                        ],
                        default=amount,
                        min=0,
                        max=amount,
                    )
                    if value:
                        self.out.nl()
                        self.out.write_line(
                            ("cyan", "Agreed, "),
                            ("yellow", str(value)),
                            ("cyan", " units."),
                        )
                        self.out.nl(2)
                        if await yesno_prompt(
                            self.out,
                            prompt=[
                                ("green", "We'll sell them for "),
                                ("yellow", str(int(c.price * value))),
                                ("green", " credits."),
                            ],
                            default=True,
                        ):
                            player_client, port_client = (
                                await self.actions.buy_from_port(
                                    port_id=port.id, commodity=c.type.name, amount=value
                                )
                            )
                            self.game.update_player(player_client)
                            self.game.update_port(port_client)

                            self.out.nl()
                            self.out.print(
                                "You are a shrewd trader, they're all yours.",
                                color="green",
                            )
                            self.out.nl(2)
                        else:
                            self.out.nl(2)
                            self.out.print("Fine, leave then.", color="red")
                            self.out.nl(2)

                    self.out.nl()
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
            ("green", "You have "),
            ("yellow", str(self.player.credits)),
            ("green", " credits and "),
            ("yellow", str(self.player.ship.holds_free)),
            ("green", " empty cargo holds"),
        )
        self.out.nl(2)


class Events(ServerEvents):
    def __init__(self, prompt: Prompt):
        self.prompt = prompt

    # noinspection PyMethodMayBeStatic
    def on_invalid_action(self, error: str):
        self.prompt.out.error(error)
