import asyncio
from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from random import randrange

import networkx as nx
from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import UIContent, Layout
from prompt_toolkit.layout import UIControl
from prompt_toolkit.layout import Window
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType

from tspace.client.models import Player, Sector, Trader


@dataclass
class Stack:
    target: Player | Trader
    ship: str
    size: int = 1


@dataclass
class Space:
    x: int
    y: int
    stack: Stack | None = None
    selected: bool = False

    @property
    def empty(self):
        return self.stack is None

    def __hash__(self):
        return hash((self.x, self.y))


class Battlefield(UIControl):
    def __init__(self, stacks: list[Stack], sector: Sector, max_x: int, max_y: int):
        self.stacks = stacks
        self.sector = sector

        self.grid_width = max_x
        self.grid_height = max_y

        self.grid: list[list[Space]] = []
        for y in range(max_y):
            row = []
            for x in range(max_x):
                space = Space(x, y)
                row.append(space)
            self.grid.append(row)

        stacks_by_player: dict[Player, list[Stack]] = defaultdict(list)
        for stack in stacks:
            stacks_by_player[stack.target].append(stack)

        x_pos = 0
        for player, stacks in stacks_by_player.items():
            start_y = self.grid_height // 2 - len(stacks) // 2
            for stack in stacks:
                self.grid[start_y][x_pos].stack = stack
                start_y += 1
            x_pos = self.grid_width - 1

        self.key_bindings = KeyBindings()
        self.key_bindings.add("q")(lambda *_: exit(0))
        self.show_cursor = False
        self._mouse_enabled = True
        self._last_selected: Space | None = None

        self.window = Window(
            dont_extend_height=False,
            dont_extend_width=False,
            content=self,
            style="bg:black",
        )

    def _gen_graph(self, start: Space):
        g = nx.Graph(directed=False)

        for line in self.grid:
            for space in line:
                if not space.empty and space != start:
                    continue
                g.add_node(space)
                if space.x % 2 == 1:
                    mod_list = ((0, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0))
                else:
                    mod_list = ((0, -1), (1, -1), (1, 0), (0, 1), (-1, 0), (-1, -1))
                for x_mod, y_mod in mod_list:
                    x = space.x + x_mod
                    y = space.y + y_mod
                    if (
                        x < 0
                        or y < 0
                        or x >= self.grid_width
                        or y >= self.grid_height
                        or (x_mod == 0 and y_mod == 0)
                    ):
                        continue

                    edge_space = self.grid[y][x]
                    if edge_space.empty:
                        g.add_edge(space, self.grid[y][x])
        return g

    def mouse_handler(self, mouse_event: MouseEvent) -> None:
        if not self._mouse_enabled:
            return None

        if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
            x, y = mouse_event.position.x, mouse_event.position.y
            space = self.get_space(x, y)
            if space is not None:
                if self._last_selected:
                    if not self._last_selected.stack or not space.empty:
                        return None

                    self._mouse_enabled = False

                    asyncio.create_task(
                        self.move_stack(self._last_selected.stack, space)
                    )

                elif space.stack and isinstance(space.stack.target, Player):
                    self._last_selected = space
                    space.selected = True

        return None

    async def move_stack(self, stack: Stack, space: Space) -> None:
        self._last_selected.stack = stack
        self._last_selected.selected = True
        path: list[Space] = self.plot_path(self._last_selected, space)
        for step in path[1:-1]:
            step.stack = self._last_selected.stack
            self._last_selected.stack = None
            self._last_selected.selected = False

            step.selected = True
            self._last_selected = step
            get_app().invalidate()
            await asyncio.sleep(0.1)

        space.stack = self._last_selected.stack
        self._last_selected.stack = None
        self._last_selected.selected = False
        get_app().invalidate()
        self._last_selected = None
        self._mouse_enabled = True

    def plot_path(self, start: Space, end: Space):
        g = self._gen_graph(start)
        steps: list[Space] = nx.shortest_path(g, start, end)
        return steps

    def get_space(self, screen_x: int, screen_y: int) -> Space | None:
        x: int = -1
        y: int = -1
        if screen_x % 4 != 0:
            x = screen_x // 4

        if x >= 0:
            if x % 2 == 0:
                y = screen_y // 2
            else:
                y = (screen_y - 1) // 2

        if x < 0 or y < 0:
            return None
        if y >= self.grid_height or x >= self.grid_width:
            return None

        return self.grid[y][x]

    def create_content(self, width, height):
        get_app().output.enable_mouse_support()

        def get_line(i):
            grid_bg = "bg:black"
            grid_color = f"{grid_bg} fg:blue"
            if i - 1 > self.grid_height * 2:
                return [(f"", "." * width)]
            if i - 1 == self.grid_height * 2:
                return [
                    (grid_color, "     \u2594\u2594\u2594" * (self.grid_width // 2)),
                    (grid_color, " "),
                ]

            result = []
            for i_x in range(0, self.grid_width // 2):
                if i % 2 == 0:
                    if (i - 1) == self.grid_height * 2 - 1 and i_x == 0:
                        result.append((grid_color, " \u2594\u2594\u2594\u2572"))
                    else:
                        result.append((grid_color, "\u2571\u2594\u2594\u2594\u2572"))
                    x = i_x * 2 + 1
                else:
                    x = i_x * 2
                    result.append((grid_color, "\u2572"))

                if i == 0:
                    result.append((grid_color, "   "))
                else:
                    y = (i - 1) // 2
                    # print(f"y: {y}, x: {x}, i: {i}")
                    space = self.grid[y][x]
                    if space.selected and space.stack:
                        if isinstance(space.stack.target, Player):
                            result.append(
                                (f"green {grid_bg}", _stack_to_str(space.stack))
                            )
                        else:
                            result.append(
                                (f"red {grid_bg}", _stack_to_str(space.stack))
                            )
                    else:
                        if space.stack:
                            marker = _stack_to_str(space.stack)
                        else:
                            marker = "   "
                        result.append((grid_bg, marker))

                    if i % 2 == 1:
                        result.append((grid_color, "\u2571\u2594\u2594\u2594"))

            if i == 0:
                result.append((grid_color, " "))
            if i > 0:
                if i % 2 == 0:
                    result.append((grid_color, "\u2571"))
                else:
                    result.append((grid_color, "\u2572"))

            for _ in range(self.grid_width, width):
                result.append(("", " "))
            return result

        return UIContent(get_line=get_line, line_count=height)  # Something very big.

    def is_focusable(self):
        return True

    def __pt_container__(self):
        return self.window


def _stack_to_str(stack: Stack) -> str:
    chars = [stack.ship]
    if stack.size >= 10:
        chars.append(chr(0x2080 + stack.size // 10))
        chars.append(chr(0x2080 + stack.size % 10))
    else:
        chars.append(chr(0x2080 + stack.size))
        chars.append(" ")
    return "".join(chars)


def main():
    grid = Battlefield(
        stacks=[
            Stack("player1", "\u257E", size=randrange(0, 9)),
            Stack("player1", "\u257E", size=randrange(0, 99)),
            Stack("player1", "\u257E", size=randrange(0, 99)),
            Stack("player2", "\u257C", size=randrange(0, 99)),
            Stack("player2", "\u257C", size=randrange(0, 99)),
        ],
        sector=None,
        max_x=20,
        max_y=20,
    )
    layout = Layout(grid.window)

    app = Application(
        layout=layout,
        full_screen=True,
        key_bindings=grid.key_bindings,
        refresh_interval=1,
    )
    print("running")
    try:
        app.output.enable_mouse_support()
        app.run()  # You won't be able to Exit this app
    finally:
        print("finally")
        print("\x1b[?1000l")
        print("\x1b[?1015l")
        print("\x1b[?1006l")
        print("\x1b[?1003l")


if __name__ == "__main__":
    main()
