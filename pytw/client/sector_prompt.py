from typing import List

from pytw.client.game import Game
from pytw.client.instant_cmd import InstantCmd
from pytw.client.instant_cmd import InvalidSelectionError
from pytw.client.models import Sector
from pytw.client.models import SectorClient
from pytw.client.models import TraderShipClient
from pytw.client.prompts import PromptTransition
from pytw.client.prompts import PromptType
from pytw.client.stream import Fragment
from pytw.client.stream import Item
from pytw.client.stream import Row
from pytw.client.stream import Table
from pytw.client.stream import Terminal
from pytw.client.stream import print_action
from pytw.client.stream import print_grid


class Actions:
    async def move_trader(self, sector_id: int) -> SectorClient:
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
        self.instant_cmd.literal("d", default=True)(self.do_d)
        self.instant_cmd.literal(
            "p", validator=lambda _: self.player.sector.port_id is not None
        )(self.do_p)
        self.instant_cmd.literal("q")(self.do_q)
        self.instant_cmd.regex(
            "[0-9]+", max_length=len(str(game.config.sectors_count))
        )(self.do_move)

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
        print_action(self.out, "Redisplay")
        self.print_sector()

    async def do_p(self, line):
        if self.player.sector.port_id:
            self.out.nl(2)
            self.out.print("Docking...", color="red", attrs=["blink"])
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
            ("magenta", "Command ["),
            ("yellow", "TL"),
            ("magenta", "="),
            ("yellow", "00:00:00"),
            ("magenta", "]"),
            ("yellow", ":"),
            ("magenta", "["),
            ("cyan", str(s.id)),
            ("magenta", "] ("),
            ("yellow", "?=Help"),
            ("magenta", ")? : "),
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
                ("magenta", "Warping to Sector "), ("yellow", str(target_id))
            )
            self.out.nl(2)

            sector_client = await self.actions.move_trader(sector_id=target_id)
            s = self.game.update_sector(sector_client)

            self.game.player.ship.sector_id = s.id
            self.game.player.visited.add(s.id)
            self.print_sector(s)

        elif self.game.sectors[target_id]:
            self.out.write_line(
                ("magenta", "Auto-warping to Sector "), ("yellow", str(target_id))
            )
            self.out.nl(2)
            warps = self.game.plot_course(self.player.sector.id, target_id)
            for warp in warps[1:]:
                if not warp:
                    breakpoint()

                print_action(self.out, f"Warping to sector {warp.id}")
                sector_client = await self.actions.move_trader(sector_id=warp.id)
                s = self.game.update_sector(sector_client)

                self.game.player.ship.sector_id = s.id
                self.game.player.visited.add(s.id)
                self.print_sector(s)

        else:
            self.out.error("Unknown target sector")

    def print_sector(self, sector: Sector = None):

        if not sector:
            sector = self.player.sector

        data = Table(rows=[])

        data.rows.append(
            Row(
                header=Fragment("green bold", "Sector "),
                items=[
                    Item(
                        [
                            Fragment("cyan", str(sector.id)),
                            Fragment("green", " in "),
                            Fragment("blue", "uncharted space"),
                        ]
                    )
                ],
            )
        )

        if sector.planets:
            items = []
            for planet in sector.planets:
                items.append(
                    Item(
                        [
                            Fragment("fg:yellow bold", f"({planet.planet_type}) "),
                            Fragment("white", planet.name),
                        ]
                    )
                )
            data.rows.append(Row(header=Fragment("magenta", "Planets"), items=items))

        if sector.port:
            p = sector.port

            items = Item(
                [
                    Fragment("cyan", p.name),
                    Fragment("yellow", ", "),
                    Fragment("magenta", "Class "),
                    Fragment("cyan", str(p.class_number)),
                    Fragment("magenta", " ("),
                ]
            )
            items.value += p.class_name_colored
            items.value.append(Fragment("magenta", ")"))

            data.rows.append(Row(header=Fragment("green", "Port"), items=[items]))
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
                warps.append(Fragment("cyan", str(w)))
            else:
                warps += [
                    Fragment("magenta", "("),
                    Fragment("red", str(w)),
                    Fragment("magenta", ")"),
                ]
            warps.append(Fragment("green", " - "))

        data = Table(
            rows=[
                Row(
                    header=Fragment("green bold", "Warps to Sector(s)"),
                    items=[Item(warps[:-1])],
                )
            ]
        )
        print_grid(self.out, data, separator=Fragment("yellow", ": "))
        self.out.nl()

    def print_ship_enter_sector(self, ship):
        self.out.nl()
        self.out.write_line(
            ("cyan bold", ship.trader.name), ("green", " warps into th esector.")
        )
        self.out.nl()

    def print_ship_exit_sector(self, ship):
        self.out.nl()
        self.out.write_line(
            ("cyan bold", ship.trader.name), ("green", " warps out of the sector.")
        )
        self.out.nl()
