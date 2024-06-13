import textwrap
from functools import partial
from typing import Awaitable, List, Set
from typing import Callable

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout import D
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout import VSplit
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import MenuContainer
from prompt_toolkit.widgets import MenuItem

from tspace.client.models import CommodityType, Sector
from tspace.client.session import Session
from tspace.client.stream import Terminal
from tspace.client.terminal_text_area import TerminalTextArea
from tspace.client.ui.dynamic_label import DynamicLabel
from tspace.client.ui.stat_frame import StatFrame, Stat


class TerminalScene:
    def __init__(self, app: Application, writer: Callable[[str], Awaitable[None]]):
        self.app = app
        self.writer = writer
        textfield = TerminalTextArea(focus_on_click=True, width=D(min=70))
        self.buffer = textfield.buffer
        self.buffer.on_change(lambda: app.invalidate())

        self.terminal = Terminal(self.buffer)
        self.session = Session(self.terminal)

        has_ship = lambda: bool(
            self.session
            and self.session.game
            and self.session.game.player
            and self.session.game.player.ship
        )

        root_container = HSplit(
            [
                VSplit(
                    [
                        HSplit(
                            [
                                StatFrame(
                                    condition=has_ship,
                                    stats=self.get_player_stats(),
                                    title="Player",
                                    width=D(max=25),
                                ),
                                StatFrame(
                                    condition=has_ship,
                                    stats=self.get_holds_stats(),
                                    title="Holds",
                                    width=D(max=25),
                                ),
                                StatFrame(
                                    condition=has_ship,
                                    stats=self.get_ship_stats(),
                                    title="Ship",
                                    width=D(max=25),
                                ),
                            ]
                        ),
                        textfield,
                        Frame(
                            title="Map",
                            body=DynamicLabel(partial(self.get_warps_label, has_ship)),
                            width=D(max=25),
                        ),
                    ],
                    height=D(),
                ),
                VSplit(
                    [
                        Frame(body=Label(text="right bottom frame\ncontent")),
                        Frame(body=Label(text="middle frame\ncontent")),
                        Frame(body=Label(text="left bottom frame\ncontent")),
                    ],
                    padding=1,
                ),
            ],
            style="bg:black",
        )

        def do_exit():
            self.session._quit()

        menu_container = MenuContainer(
            body=root_container,
            menu_items=[
                MenuItem(
                    "File",
                    children=[MenuItem("New"), MenuItem("Exit", handler=do_exit)],
                ),
                MenuItem(
                    "Edit",
                    children=[MenuItem("Undo"), MenuItem("Cut"), MenuItem("Copy")],
                ),
                MenuItem("View", children=[MenuItem("Status Bar")]),
                MenuItem("Info", children=[MenuItem("About")]),
            ],
        )
        self.layout = Layout(menu_container, focused_element=textfield)
        self.textfield = textfield

    def get_player_stats(self) -> List[Stat]:
        player = lambda: self.session.game.player
        return [
            Stat(title="Name", callable=lambda: player().name),
            Stat(
                title="Port",
                callable=lambda: "" if not player().port else player().port.class_name,
            ),
            Stat(title="Credits", callable=lambda: player().credits),
        ]

    def get_holds_stats(self) -> List[Stat]:
        ship = lambda: self.session.game.player.ship
        return [
            Stat(
                title="Total",
                callable=lambda: ship().holds_capacity - ship().holds_free,
            ),
            Stat(
                title="Fuel Ore", callable=lambda: ship().holds[CommodityType.fuel_ore]
            ),
            Stat(
                title="Organics", callable=lambda: ship().holds[CommodityType.organics]
            ),
            Stat(
                title="Equipment",
                callable=lambda: ship().holds[CommodityType.equipment],
            ),
            Stat(title="Empty", callable=lambda: ship().holds_free),
        ]

    def get_ship_stats(self) -> List[Stat]:
        ship = lambda: self.session.game.player.ship
        return [
            Stat(title="Name", callable=lambda: ship().name),
            Stat(title="Type", callable=lambda: ship().type),
        ]

    def get_warps_label(self, condition: Callable[[], bool]):
        frags = []
        if condition():
            sector = self.session.game.player.sector
            rows = self._calculate_max_rows(sector)

            if len(rows) > 40:
                max_depth = 2
            else:
                max_depth = 3

            # frags.append(("", f"len: {len(rows)}\n"))
            # frags.append(("", "\n".join(textwrap.wrap(f"rows: {','.join([str(r) for r in rows])}", 15))))
            visited = set()
            visited.add(sector.id)
            frags += self.print_sector(sector)
            frags.append(("", "\n"))
            for idx, warp in enumerate(sector.warps):
                frags += self._append_sector_warps(
                    warp, max_depth, 1, visited, last=idx == len(sector.warps) - 1
                )
        return FormattedText(frags)

    def _calculate_max_rows(self, sector):
        rows = []
        visited = set()
        visited.add(sector.id)
        for d1 in sector.warps:
            not_visited = d1 not in visited
            if self.session.game.sectors[d1].warps:
                visited.add(d1)
            rows.append(d1)
            if not_visited:
                for d2 in self.session.game.sectors[d1].warps:
                    not_visited = d2 not in visited
                    if self.session.game.sectors[d2].warps:
                        visited.add(d2)
                    rows.append(d2)
                    if not_visited:
                        for d3 in self.session.game.sectors[d2].warps:
                            rows.append(d3)
        return rows

    def _append_sector_warps(
        self,
        sector_id,
        max_depth: int,
        depth: int,
        visited: Set[int],
        last: bool = False,
    ) -> List:
        frags = []
        not_visited = not sector_id in visited

        w = self.session.game.sectors[sector_id]
        show_children = depth < max_depth and w.warps and not_visited
        if show_children:
            visited.add(sector_id)

        frags.append(("grey", "\u2502 " * (depth - 1)))
        if last and not show_children:
            frags.append(("grey", "\u2514 "))
        else:
            frags.append(("grey", "\u251C "))

        frags += self.print_sector(w)

        if show_children:
            frags.append(("", "\n"))
            # frags.append(("", " " * depth))
            # frags.append(("gray", "\\\n"))

            for idx, child_warp_id in enumerate(w.warps):
                last = idx == len(w.warps) - 1
                frags += self._append_sector_warps(
                    child_warp_id, max_depth, depth + 1, visited, last
                )
        elif w.warps:
            frags.append(("gray", "\u2026"))
            frags.append(("", "\n"))
        else:
            frags.append(("", "\n"))
        return frags

    def print_sector(self, sector: Sector):
        frags = []
        if sector.id in self.session.game.player.visited:
            frags.append(("cyan", str(sector.id)))
        else:
            frags.append(("red", f"({sector.id})"))
        if sector.ports:
            frags.append(("", " "))
            frags.append(("magenta", "("))
            frags += [(f.style, f.text) for f in sector.ports[0].class_name_colored]
            frags.append(("magenta", ")"))
        return frags

    async def start(self):
        return await self.session._start(self.writer)

    def end(self):
        pass
