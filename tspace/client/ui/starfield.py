import asyncio
from random import randrange

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import UIContent
from prompt_toolkit.layout import UIControl
from prompt_toolkit.layout import Window


class Starfield(UIControl):
    """
    Based on http://codentronix.com/2011/05/28/3d-starfield-made-using-python-and-pygame/
    """

    def __init__(self, num_stars: int = 256, max_depth: int = 12):
        self.num_stars = num_stars
        self.max_depth = max_depth

        self.key_bindings = KeyBindings()
        self.show_cursor = False

        self.window = Window(
            dont_extend_height=False,
            dont_extend_width=False,
            content=self,
            style="bg:black",
        )
        self.init_stars()
        self.speed = 0.03
        self.paused = False

    def reset_speed(self):
        self.speed = 0.03

    def init_stars(self):
        """ Create the starfield """
        self.stars = []
        for i in range(self.num_stars):
            # A star is represented as a list with this format: [X,Y,Z]
            star = [randrange(-5, 5), randrange(-5, 5), randrange(1, self.max_depth)]
            self.stars.append(star)

    def move_stars(self, width, height):
        """ Move and draw the stars """
        origin_x = width / 2
        origin_y = height / 2

        screen = [None] * height
        for y in range(height):
            row = [("", " ")] * width
            screen[y] = row

        for star in self.stars:
            # The Z component is decreased on each frame.
            star[2] -= self.speed

            # If the star has past the screen (I mean Z<=0) then we
            # reposition it far away from the screen (Z=max_depth)
            # with random X and Y coordinates.
            if star[2] <= 0:
                star[0] = randrange(-5, 5)
                star[1] = randrange(-5, 5)
                star[2] = self.max_depth

            # Convert the 3D coordinates to 2D using perspective projection.
            k = 128.0 / star[2]
            x = int(star[0] * k + origin_x)
            y = int(star[1] * k + origin_y)

            if 0 <= x < width and 0 <= y < height:
                size = (1 - float(star[2]) / self.max_depth) * 5
                shade = (1 - float(star[2]) / self.max_depth) * 255
                # print(f"star {id}: {x},{y}")

                hex_part = hex(round(shade))[2:]
                if len(hex_part) == 1:
                    hex_part = f"0{hex_part}"

                hex_shade = hex_part * 3

                dot = "."
                if size > 3.5:
                    parts = []
                    for _ in range(3):
                        val = hex(randrange(0, 255))[2:]
                        if len(val) == 1:
                            parts.append(f"0{val}")
                        else:
                            parts.append(val)
                    hex_shade = "".join(parts)
                    # print(f"shade: {hex_shade}")
                    dot = "\u26AB"
                elif size > 3:
                    dot = "o"
                elif size > 2:
                    dot = "*"
                # print(f"size:{size}")

                screen[y][x] = (f"#{hex_shade}", dot)
                # self.screen.fill((shade, shade, shade), (x, y, size, size))

        return screen

    def create_content(self, width, height):
        screen = self.move_stars(width, height)

        def get_line(i):
            result = screen[i]
            return result

        return UIContent(get_line=get_line, line_count=height)  # Something very big.

    def is_focusable(self):
        return False

    def __pt_container__(self):
        return self.window
