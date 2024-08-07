import asyncio
import sys
from typing import List

from tspace.client.game import Game
from tspace.client.instant_cmd import InstantCmd
from tspace.client.instant_cmd import InvalidSelectionError
from tspace.client.models import Sector
from tspace.client.prompts import PromptTransition
from tspace.client.prompts import PromptType
from tspace.client.stream import Fragment
from tspace.client.stream import Item
from tspace.client.stream import Row
from tspace.client.stream import Table
from tspace.client.terminal import Terminal
from tspace.client.stream import print_action
from tspace.client.stream import print_grid
from tspace.client.ui.warp import WarpDialog
from tspace.common.events import ServerEvents
from tspace.common.models import TraderShipPublic, SectorPublic, BattlePublic
from tspace.common.actions import SectorActions


# noinspection PyMethodMayBeStatic,PyIncorrectDocstring
class Prompt(ServerEvents):
    def __init__(self, game: Game, actions: SectorActions, term: Terminal):
        self.out = term
        self.player = game.player
        self.actions = actions
        self.game = game

        self.instant_cmd = InstantCmd(term)
        self.instant_cmd.literal("d", default=True)(self.do_d)
        self.instant_cmd.literal(
            "p", validator=lambda _: len(self.player.sector.ports) > 0
        )(self.do_p)
        self.instant_cmd.literal(
            "a", validator=lambda _: len(self.player.sector.ships) > 1
        )(self.do_a)
        self.instant_cmd.literal("q")(self.do_q)
        self.instant_cmd.regex("[0-9]+", max_length=sys.maxsize)(self.do_move)

    async def on_ship_enter_sector(self, sector: SectorPublic, ship: TraderShipPublic):
        self.game.update_sector(sector)
        if self.player.ship.sector.id == sector.id:
            self.print_ship_enter_sector(ship)

    async def on_ship_exit_sector(self, sector: SectorPublic, ship: TraderShipPublic):
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
        self.out.nl(2)
        self.out.print("Docking...", color="red", attrs=["blink"])
        player, port = await self.actions.enter_port(
            port_id=self.player.sector.ports[0].id
        )
        p = self.game.update_port(port)
        self.game.update_player(player)
        self.game.player.port_id = p.id

        raise PromptTransition(PromptType.PORT)

    async def do_a(self, line):
        self.out.nl(2)
        self.out.print("<Attack>", color="red", attrs=["blink"])
        self.out.nl(2)
        for ship in (
            s for s in self.player.sector.ships if s.trader.id != self.player.id
        ):
            self.out.write_line(
                ("green", "Attack "),
                ("cyan", f"{ship.trader.name}'s "),
                ("blue", f"{ship.ship_type.name} "),
                ("cyan bold", f"({ship.relative_strength.value})"),
            )
            do_attack = await InstantCmd.yes_no(self.out)
            if do_attack:
                self.out.write_line(("red", "Attacking..."))
                await self.actions.enter_battle(self.player.ship_id, ship.id)
                raise PromptTransition(PromptType.BATTLE)

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

            dialog = WarpDialog(target_id)
            dialog_task = asyncio.create_task(dialog.show())
            # get_app().invalidate()
            # await self.beams_animated_prompt(f"<< Warping to Sector {target_id} >>")
            self.out.nl(2)
            # self.out.write_line(
            #     ("magenta", "Warping to Sector "), ("yellow", str(target_id))
            # )
            # self.out.nl(2)

            sector_client = await self.actions.move_trader(sector_id=target_id)
            s = self.game.update_sector(sector_client)
            dialog.set_next_sector(s)
            await dialog_task

            self.game.player.ship.sector_id = s.id
            self.game.player.visited.add(s.id)
            self.print_sector(s)

        elif self.game.sectors.get(target_id):
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

        if sector.ports:
            items = []
            for port in sector.ports:
                item = Item(
                    [
                        Fragment("cyan", port.name),
                        Fragment("yellow", ", "),
                        Fragment("magenta", "Class "),
                        Fragment("cyan", str(port.class_number)),
                        Fragment("magenta", " ("),
                    ]
                )
                item.value += port.class_name_colored
                item.value.append(Fragment("magenta", ")"))
                items.append(item)
            data.rows.append(Row(header=Fragment("green", "Port"), items=items))

        other_ships = [s for s in sector.ships if s.trader.id != self.player.id]
        if other_ships:
            ship_items = []
            for ship in other_ships:
                item = Item(
                    [
                        Fragment("red", ship.trader.name),
                        Fragment("yellow", ", "),
                        Fragment("green", "in "),
                        Fragment("cyan", ship.name),
                        Fragment("green", f" ({ship.ship_type.name})"),
                    ]
                )
                ship_items.append(item)
            data.rows.append(Row(header=Fragment("yellow", "Ships"), items=ship_items))

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
            ("cyan bold", ship.trader.name), ("green", " warps into the sector.")
        )
        self.out.nl()

    def print_ship_exit_sector(self, ship):
        self.out.nl()
        self.out.write_line(
            ("cyan bold", ship.trader.name), ("green", " warps out of the sector.")
        )
        self.out.nl()
