import math

import kivy
from kivy.core.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from pytw.moves import ShipMoves

from pytw.planet import Galaxy


kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line, Rectangle


class SectorCircle(Widget):
    def __init__(self, sector):
        super().__init__()
        self.sector = sector


class Universe(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(1, 1, 1, 1) # green; colors range from 0-1 instead of 0-255
            self.rect = Rectangle(size=self.size,
                                  pos=self.pos)

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        # listen to size and position changes
        self.bind(pos=update_rect, size=update_rect)

        self.game = Galaxy(1, "foo", 5)
        self.game.start()
        self.player = self.game.add_player("Bob")
        self.moves = ShipMoves(self.player, self.game)
        ship_image = Image("assets/merchant_cruiser.gif")
        stars_image = Image("assets/stars.jpg")

        def draw_uni(*args):
            with self.canvas.before:
                Rectangle(pos=self.pos, size=self.size, texture=stars_image.texture)

            with self.canvas:
                Color(.3, .3, .3, mode='hsv')
                size = 70
                centerx = int(size * self.game.diameter + size)
                centery = int(size * self.game.diameter)

                def sector_to_pixel(sector):
                    x, y = sector.coords
                    x_offset = 0 if y == 0 else math.fabs(y) * size * (math.fabs(y) / y)
                    return x * (size * 2) + int(size / 2) + centerx + x_offset, y * (size * 2) + int(size / 2) + centery

                for sector in self.game.sectors.values():
                    for warp_id in sector.warps:
                        if self.player.has_visited(sector.sector_id):
                            Line(points=sector_to_pixel(sector) + sector_to_pixel(self.game.sectors[warp_id]), width=1)

                for sector in self.game.sectors.values():
                    x, y = sector_to_pixel(sector)
                    disabled = False
                    if self.player.has_visited(sector.sector_id):
                        Color(.2, .5, .8)
                    else:
                        for src in self.game.sectors.values():
                            if sector.sector_id in src.warps and self.player.has_visited(src.sector_id):
                                Color(.7, .5, .8)
                                break
                        else:
                            disabled = True
                            Color(.2, .5, .2)
                    Ellipse(pos=(x - size/2, y - size/2), size=(size, size))
                    if sector.ships:
                        Color(.6, .2, .3)
                        Rectangle(texture=ship_image.texture, pos=(x - size/4, y - size/4), size=(int(size/2), int(size/2)))

                    Color(0, 0, 0, mode='hsv')
                    # noinspection PyArgumentList
                    Line(circle=(x, y, size/2))
                    Color(1, 1, 1)
                    btn_width = int(math.sqrt(size * size / 2))

                    def btn_clicked(instance):
                        value = instance.text
                        self.moves.move_sector(self.player.current_ship_id, int(value))
                        draw_uni()

                    btn = Button(pos=(x - size / 2 + ((size - btn_width) / 2), y - size / 2 + ((size - btn_width) / 2)), size=(btn_width, btn_width), size_hint=(None, None), background_normal='', background_color=(.3, .3, .4, .0), text="{}".format(sector.sector_id))
                    if disabled:
                        btn.disabled = True
                    btn.bind(on_press=btn_clicked)
                    self.add_widget(btn)

        draw_uni()

        self.bind(pos=draw_uni, size=draw_uni)

            # for n in g.nodes_iter():
            #     draw.text(node_to_pixel(n), str(n), fill='black')
            # image.show()
            #
            # Ellipse(pos=(50, 50), size=(20, 20))


class TestApp(App):

    def build(self):
        # create a button, and  attach animate() method as a on_press handler
        return Universe()

if __name__ == '__main__':
    TestApp().run()