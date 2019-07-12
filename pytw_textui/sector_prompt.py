from typing import List

from pytw_textui.game import Game
from pytw_textui.instant_cmd import InstantCmd
from pytw_textui.instant_cmd import InvalidSelectionError
from pytw_textui.models import Sector
from pytw_textui.models import SectorClient
from pytw_textui.models import TraderShipClient
from pytw_textui.prompts import PromptTransition
from pytw_textui.prompts import PromptType
from pytw_textui.stream import Fragment
from pytw_textui.stream import Item
from pytw_textui.stream import Row
from pytw_textui.stream import Table
from pytw_textui.stream import Terminal
from pytw_textui.stream import print_action
from pytw_textui.stream import print_grid


class Actions:
    async def move_trader(self, sector_id: int):
        pass

    async def enter_port(self, port_id: int):
        pass


# noinspection PyMethodMayBeStatic,PyIncorrectDocstring
class Prompt:
    def __init__(self, game: Game, actions: Actions, term: Terminal):
        self.out = term
        self.player = game.player
        self.actions = actions
        self.game = game

        self.instant_cmd = InstantCmd(term)
        self.instant_cmd.literal('d', default=True)(self.do_d)
        self.instant_cmd.literal('p', validator=lambda _: self.player.sector.port_id is not None)(self.do_p)
        self.instant_cmd.literal('q')(self.do_q)
        self.instant_cmd.regex('[0-9]+', max_length=len(str(game.config.sectors_count)))(self.do_move)

    async def on_ship_enter_sector(self, sector: SectorClient, ship: TraderShipClient):
        self.game.update_sector(sector)
        if self.player.ship.sector.id == sector.id:
            self.print_ship_enter_sector(ship)

    async def on_ship_exit_sector(self, sector: SectorClient, ship: TraderShipClient):
        self.game.update_sector(sector)
        if self.player.ship.sector.id == sector.id:
            self.print_ship_exit_sector(ship)

    # noinspection PyUnusedLocal
    async def do_d(self, line):
        """
        Re-display the current sector
        """
        print_action(self.out, 'Redisplay')
        self.print_sector()

    async def do_p(self, line):
        if self.player.sector.port_id:
            self.out.nl(2)
            self.out.print("Docking...", color='red', attrs=['blink'])
            await self.actions.enter_port(port_id=self.player.sector.port.sector_id)
            raise PromptTransition(PromptType.NONE)

    def do_q(self, line):
        raise PromptTransition(PromptType.QUIT)

    async def cmdloop(self):
        while True:
            try:
                self.out.write_line(*self.prompt)
                return await self.instant_cmd.cmdloop()
            except InvalidSelectionError:
                self.out.nl()

    @property
    def prompt(self):
        s = self.player.ship.sector
        return (
            ('magenta', 'Command ['),
            ('yellow', 'TL'),
            ('magenta', '='),
            ('yellow', '00:00:00'),
            ('magenta', ']'),
            ('yellow', ':'),
            ('magenta', '['),
            ('cyan', str(s.id)),
            ('magenta', '] ('),
            ('yellow', '?=Help'),
            ('magenta', ')? : ')
        )

    async def do_move(self, target_sector):
        """
        Move to an adjacent sector
        """
        try:
            target_id = int(target_sector)
        except ValueError:
            self.out.error("Invalid sector number")
            return

        print_action(self.out, "Move")
        if target_id in self.player.sector.warps:
            self.out.write_line(
                ('magenta', 'Warping to Sector '),
                ('yellow', str(target_id))
            )
            self.out.nl(2)

            await self.actions.move_trader(sector_id=target_id)
            raise PromptTransition(next_prompt=PromptType.NONE)
        elif self.game.sectors[target_id]:
            self.out.write_line(
                ('magenta', 'Auto-warping to Sector '),
                ('yellow', str(target_id))
            )
            self.out.nl(2)
            warps = self.game.plot_course(self.player.sector.id, target_id)
            for warp in warps[1:]:
                if not warp:
                    breakpoint()
                await self.actions.move_trader(sector_id=warp.id)

            raise PromptTransition(next_prompt=PromptType.NONE)
        else:
            self.out.error("Unknown target sector")

    def print_sector(self, sector: Sector = None):

        if not sector:
            sector = self.player.sector

        data = Table(rows=[])

        data.rows.append(Row(
            header=Fragment("green bold", "Sector "),
            items=[Item([
                Fragment("cyan", str(sector.id)),
                Fragment("green", " in "),
                Fragment("blue", "uncharted space")
            ])]
        ))

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

            items = Item([
                Fragment("cyan", p.name),
                Fragment("yellow", ", "),
                Fragment("magenta", "Class "),
                Fragment("cyan", str(p.class_number)),
                Fragment("magenta", " ("),
            ])
            items.value += p.class_name_colored
            items.value.append(Fragment("magenta", ")"))

            data.rows.append(Row(
                header=Fragment("green", "Port"),
                items=[items]
            ))
        #
        # other_ships = [s for s in sector.ships if s.trader.id != self.player.ship.id]
        # if other_ships:
        #     lines = []
        #     for ship in other_ships:
        #         lines.append(Color("{red}{trader}{/red}{yellow},{/yellow}").format(trader=ship.trader.name))
        #         lines.append(Color("{green}in{/green} {cyan}{ship}{/cyan} {green}({ship_type}){/green}").format(
        #                 ship=ship.name,
        #                 ship_type="unknown"
        #         ))
        #     data.append((Color.yellow("Ships"), lines))

        print_grid(self.out, data, separator=Fragment("yellow", ": "))

        warps: List[Fragment] = []
        for w in sector.warps:
            if w in self.player.visited:
                warps.append(Fragment('cyan', str(w)))
            else:
                warps += [Fragment('magenta', '('),
                          Fragment('red', str(w)),
                          Fragment('magenta', ')')]
            warps.append(Fragment('green', ' - '))

        data = Table(rows=[
            Row(header=Fragment("green bold", "Warps to Sector(s)"),
                items=[Item(warps[:-1])])
        ])
        print_grid(self.out, data, separator=Fragment("yellow", ": "))
        self.out.nl()

    def print_ship_enter_sector(self, ship):
        self.out.nl()
        self.out.write_line(
            ('cyan bold', ship.trader.name),
            ('green', ' warps into th esector.')
        )
        self.out.nl()

    def print_ship_exit_sector(self, ship):
        self.out.nl()
        self.out.write_line(
            ('cyan bold', ship.trader.name),
            ('green', ' warps out of the sector.')
        )
        self.out.nl()
