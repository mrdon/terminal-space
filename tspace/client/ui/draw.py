import random
from copy import deepcopy
from enum import Enum
from functools import cache

from PIL import Image, ImageDraw
from prompt_toolkit import ANSI
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.layout import UIContent
from prompt_toolkit.layout import UIControl
from prompt_toolkit.layout import Window

from tspace.client.logging import log


class C(Enum):
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"
    BRIGHT_BLACK = "\033[1;30m"
    BRIGHT_RED = "\033[1;31m"
    BRIGHT_GREEN = "\033[1;32m"
    BRIGHT_YELLOW = "\033[1;33m"
    BRIGHT_BLUE = "\033[1;34m"
    BRIGHT_MAGENTA = "\033[1;35m"
    BRIGHT_CYAN = "\033[1;36m"
    BRIGHT_WHITE = "\033[1;37m"
    RESET = "\033[0m"


class G(Enum):
    SPACE = " "
    DOT = "."
    LIGHT = "\u2591"
    MEDIUM = "\u2592"
    DARK = "\u2593"
    BLOCK = "\u2588"


TRANS = (0, 0, 0, 0)
COLORS = [c for c in C]
GLYPHS = [g for g in G]


@cache
def rgb(c: C, g: G = G.BLOCK) -> tuple[int, int, int, int]:
    return COLORS.index(c), GLYPHS.index(g), 255, 255


@cache
def from_rgb(value: tuple[int, int, int, int]) -> tuple[C, G]:
    return COLORS[value[0]], GLYPHS[value[1]]


@cache
def gen_frames(
    width: int, height: int, steps: int, port: bool, planet: bool
) -> list[list[str]]:
    log.info(f"Rendering w:{width} h:{height} steps:{steps}")
    frames = []
    bg = stars(width, height)
    max_scale = 1.0
    min_scale = 0.2
    scale = min_scale
    speed = (max_scale - min_scale) / steps

    for _ in range(steps):
        if planet:
            g = gen_planet(1 + 0.2 * scale, (width, height), (0.5, 1.3), bg=bg)
        else:
            g = bg

        if port:
            result = gen_port(scale, (width, height), (0.6, 0.6), bg=g)
        else:
            result = g
        scale = min(max_scale, scale + speed)
        frames.append(
            [to_formatted_text(ANSI("".join(line_parts))) for line_parts in result]
        )
    return frames


class AnimatedPlanetApproach(UIControl):
    def __init__(self, secs: int, port: bool, planet: bool):
        self.show_cursor = False
        self._port = port
        self._planet = planet
        self.steps = secs * get_app().fps

        self.window = Window(
            dont_extend_height=False,
            dont_extend_width=False,
            content=self,
            style="bg:black",
        )
        self.frame = 0

    @cache
    def _stars(self, width: int, height: int):
        return stars(width, height)

    def next_frame(self, width: int, height: int):
        frames = gen_frames(width, height, self.steps, self._port, self._planet)
        result = frames[self.frame]
        self.frame = min(self.steps - 1, self.frame + 1)
        return result

    def create_content(self, width, height):
        screen = self.next_frame(width, height)

        def get_line(i):
            try:
                result = screen[i]
            except IndexError:
                return []
            return result

        return UIContent(get_line=get_line, line_count=height)  # Something very big.

    def is_focusable(self):
        return False

    def __pt_container__(self):
        return self.window


def stars(width: int, height: int) -> list[list[str]]:
    bg = []
    for y in range(height):
        bg.append([])
        for x in range(width):
            if random.randint(0, 20) == 1:
                color = C.WHITE if random.randint(1, 3) == 1 else C.BRIGHT_WHITE
                bg[y].append(f"{color.value}.{C.RESET.value}")
            else:
                bg[y].append(" ")

    return bg


def gen_planet(
    scale: float,
    size: tuple[int, int],
    center_mod: tuple[float, float] = (0.5, 0.5),
    bg: list[list[str]] | None = None,
) -> list[list[str]]:

    # log.info(f"x: {width}, y: {height}, distance: {distance}")
    width, height = size
    img = Image.new("RGBA", (width, height), TRANS)
    draw = ImageDraw.Draw(img)

    center_y = int(height * center_mod[1])
    y_radius = int(height * 0.6) * scale
    center_x = int(width * center_mod[0])
    x_radius = int(width * 0.8) * scale

    draw.ellipse(
        (
            center_x - x_radius,
            center_y - y_radius,
            center_x + x_radius,
            center_y + y_radius,
        ),
        fill=rgb(C.CYAN, G.BLOCK),
        outline=rgb(C.BRIGHT_CYAN, G.LIGHT),
    )
    return _render_image(bg, img)


def gen_port(
    scale: float,
    size: tuple[int, int],
    center_mod: tuple[float, float] = (0.5, 0.5),
    bg: list[list[str]] | None = None,
) -> list[list[str]]:

    # log.info(f"x: {width}, y: {height}, distance: {distance}")
    width, height = size
    img = Image.new("RGBA", (width, height), TRANS)
    draw = ImageDraw.Draw(img)

    center_y = int(height * center_mod[1])
    y_radius = int(height * 0.2) * scale
    center_x = int(width * center_mod[0])
    x_radius = int(width * 0.2) * scale
    stem_width = int(x_radius * 0.3)

    draw.line(
        (center_x, center_y - int(y_radius * 1.3), center_x, center_y + y_radius * 3),
        width=stem_width,
        fill=rgb(C.BRIGHT_BLACK, G.BLOCK),
    )
    draw.line(
        (center_x, center_y - int(y_radius * 1.3), center_x, center_y + y_radius * 3),
        width=stem_width - 1,
        fill=rgb(C.BRIGHT_BLACK, G.MEDIUM),
    )
    draw.ellipse(
        (
            center_x - x_radius,
            center_y - y_radius,
            center_x + x_radius,
            center_y + y_radius,
        ),
        fill=rgb(C.MAGENTA, G.BLOCK),
        outline=rgb(C.MAGENTA, G.MEDIUM),
    )

    inner_x_radius = int(x_radius / 2)
    inner_y_radius = int(y_radius / 2)
    draw.ellipse(
        (
            center_x - inner_x_radius,
            center_y - inner_y_radius,
            center_x + inner_x_radius,
            center_y + inner_y_radius,
        ),
        fill=TRANS,
        outline=rgb(C.MAGENTA, G.LIGHT),
    )
    draw.line(
        (
            center_x,
            center_y - int(y_radius * 2),
            center_x,
            center_y + int(y_radius / 2),
        ),
        width=stem_width,
        fill=rgb(C.BRIGHT_BLACK, G.MEDIUM),
    )
    draw.line(
        (
            center_x,
            center_y - int(y_radius * 2.5),
            center_x,
            center_y + int(y_radius / 2),
        ),
        width=stem_width - 1,
        fill=rgb(C.BRIGHT_BLACK, G.BLOCK),
    )
    draw.line(
        (
            center_x,
            center_y - int(y_radius * 3),
            center_x,
            center_y + int(y_radius / 2),
        ),
        width=stem_width - 2,
        fill=rgb(C.BRIGHT_BLACK, G.BLOCK),
    )
    img = img.rotate(45)

    return _render_image(bg, img)

    # for y in range(len(ascii_img)):
    #     for x in range(len(ascii_img[y])):
    #         print(ascii_img[y][x], end="")
    #     print()


def _render_image(bg, img: Image.Image) -> list[list[str]]:
    ascii_img = []
    for y in range(img.height):
        ascii_img.append([])
        for x in range(img.width):
            img_c = img.getpixel((x, y))
            if img_c == TRANS:
                ascii_img[y].append(" " if bg is None else bg[y][x])
                continue

            c, g = from_rgb(img_c)
            ascii_img[y].append(f"{c.value}{g.value}{C.RESET.value}")
    return ascii_img


def merge(bg: list[list[str]], fg: list[list[str]]) -> list[list[str]]:

    result = deepcopy(bg)
    for y in range(len(bg)):
        for x in range(len(bg[y])):
            cur = fg[y][x]
            result[y][x] = bg[y][x] if cur == " " else cur
    return result


def sizes(func, w: int, h: int):
    bg = stars(w, h)

    for scale in (0.1, 0.5, 1):
        g = func(scale, (w, h), (0.5, 0.5), bg=bg)
        for y in range(len(g)):
            for x in range(len(g[y])):
                print(g[y][x], end="")
            print()


def comp(w: int, h: int):
    bg = stars(w, h)

    for scale in (0.1, 0.5, 1):
        g = gen_planet(1 + 0.2 * scale, (w, h), (0.5, 1.3), bg=bg)
        g = gen_port(scale, (w, h), (0.6, 0.6), bg=g)
        for y in range(len(g)):
            for x in range(len(g[y])):
                print(g[y][x], end="")
            print()


if __name__ == "__main__":
    comp(90, 50)
