import random
from io import BytesIO

from PIL import Image, ImageDraw


import asyncio
from random import randrange

from prompt_toolkit import ANSI
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import UIContent
from prompt_toolkit.layout import UIControl
from prompt_toolkit.layout import Window

from tspace.client.logging import log


class AnimatedPlanetApproach(UIControl):
    def __init__(self, steps: int = 10):
        self.show_cursor = False
        self.steps = steps

        self.window = Window(
            dont_extend_height=False,
            dont_extend_width=False,
            content=self,
            style="bg:black",
        )
        self.speed = 0.11
        self._current_distance = 10

    def next_frame(self, width: int, height: int):
        result = planet(self._current_distance, width, height)
        self._current_distance -= self.speed
        return result

    def create_content(self, width, height):
        screen = self.next_frame(width, height)

        def get_line(i):
            try:
                result = screen[i]
            except IndexError:
                return []
            return to_formatted_text(ANSI("".join(result)))

        return UIContent(get_line=get_line, line_count=height)  # Something very big.

    def is_focusable(self):
        return False

    def __pt_container__(self):
        return self.window


def planet(distance: int, width: int, height: int) -> list[list[str]]:
    log.info(f"x: {width}, y: {height}, distance: {distance}")
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)
    center_y = int(width * .5) + int(distance * 1.2)
    y_radius = int(height * .6) - int(distance * .6)
    x_radius = width - int(width * .4) - distance
    center_x = width / 2

    draw.ellipse((center_x - x_radius, center_y - y_radius, center_x + x_radius, center_y +
                  y_radius),
                 fill=(255, 0, 0),
                 outline=(255, 255, 255))
    ascii_img = []

    random.seed(width + height)
    bg = []
    for y in range(img.height):
        bg.append([])
        for x in range(img.width):
            if random.randint(0, 20) == 1:
                color = "0" if random.randint(1, 3) == 1 else "1"
                bg[y].append(f"\033[{color};37m.\033[0m")
            else:
                bg[y].append(" ")

    for y in range(img.height):
        ascii_img.append([])
        for x in range(img.width):
            match img.getpixel((x, y)):
                case (255, 0, 0):
                    ascii_img[y].append("\033[0;34m\u2588\033[0m")
                case (255, 255, 255):
                    ascii_img[y].append(u"\033[1;34m\u2591\033[0m")
                case _:
                    ascii_img[y].append(bg[y][x])
    return ascii_img

    # for y in range(len(ascii_img)):
    #     for x in range(len(ascii_img[y])):
    #         print(ascii_img[y][x], end="")
    #     print()


if __name__ == "__main__":
    planet(10)
    print()
    planet(5)
    print()
    planet(0)
