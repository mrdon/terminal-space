import random
import math
from PIL import Image
from PIL.ImageDraw import Draw
import networkx as nx
from networkx.algorithms import shortest_path_length


def gen_hex_center(size):
    g = nx.Graph(directed=False)
    g.add_node((0, 0))

    radius = math.ceil(size / 2)
    for rad in range(radius):
        for q, r in g.nodes():
            g.add_edge((q, r), (q, r - 1))
            g.add_edge((q, r), (q - 1, r))
            g.add_edge((q, r), (q - 1, r + 1))
            g.add_edge((q, r), (q, r + 1))
            g.add_edge((q, r), (q + 1, r - 1))
            g.add_edge((q, r), (q + 1, r))

    print("radius: {}".format(radius))

    for x in range(radius):
        g.add_edge((x * -1, radius), (x * -1 - 1, radius))
        g.add_edge((x, -1 * radius), (x + 1, -1 * radius))
        g.add_edge((radius, x * -1), (radius, x * -1 - 1))
        g.add_edge((radius * -1, x), (-1 * radius, x + 1))
        g.add_edge((x * -1, radius * -1 + x), (x * -1 - 1, radius * -1 + x + 1))
        g.add_edge((x, radius - x), (x + 1, radius - x - 1))

    return g.to_directed()


def gen_2d_grid(size):
    g = nx.grid_2d_graph(size, size)
    x = y = n = 0
    for n in g:
        x, y = n
    if x > 0 and y > 0:
        g.add_edge(n, (x - 1, y - 1))
    if x < size - 1 and y < size - 1:
        g.add_edge(n, (x + 1, y + 1))

    return g.to_directed()


def remove_warps(g):
    target_edge_count = int(g.number_of_nodes() * density)
    print("num: {} : {}".format(target_edge_count, nx.number_of_edges(g)))
    edges = nx.edges(g)
    removed_edges = []
    while len(edges) > target_edge_count:
        e = random.choice(edges)
        if len(g.neighbors(e[0])) > 1 and len(g.neighbors(e[1])) > 1:
            # print("Removing edge: {}".format(e))
            g.remove_edge(*e)
            edges.remove(e)
            other = e[::-1]
            g.remove_edge(*other)
            edges.remove(other)
            removed_edges += [e, other]
            # print("Removing edge: {} : {}".format(e, other))

    print("calculating from base")

    while True:
        print("pass ----------- ")
        connected = True
        for n in g.nodes_iter():
            try:
                shortest_path_length(g, source=(0, 0), target=n)
            except nx.exception.NetworkXNoPath:
                connected = False
                print('no path {}, adding back'.format(n))
                for e in list(removed_edges):
                    src, target = e
                    if target == n:
                        g.add_edge(src, target)
                        g.add_edge(target, src)
                        try:
                            shortest_path_length(g, source=(0, 0), target=n)
                            removed_edges.remove((src, target))
                            removed_edges.remove((target, src))
                            print("Added back {}".format((src, target)))
                            break
                        except nx.exception.NetworkXNoPath:
                            g.remove_edge(src, target)
                            g.remove_edge(target, src)
        if connected:
            break

    print("double checking")
    warps = [0] * 7
    for n in g.nodes_iter():
        try:
            shortest_path_length(g, source=(0, 0), target=n)
            warps[len(nx.neighbors(g, n))] += 1
        except nx.exception.NetworkXNoPath:
            raise Exception("bad")

    nodes_len = g.number_of_nodes()
    print("Warps:")
    for ind, num in enumerate(warps):
        print(" {} - {}%".format(ind, int((num / nodes_len) * 100)))
    print('Done')


def draw_hex_grid(g):
    class HexagonGenerator(object):
        """Returns a hexagon generator for hexagons of the specified size."""

        def __init__(self, edge_length):
            self.edge_length = edge_length

        @property
        def col_width(self):
            return self.edge_length * 3

        @property
        def row_height(self):
            return math.sin(math.pi / 3) * self.edge_length

        def __call__(self, r, c):
            x = (c + 0.5 * (r % 2)) * self.col_width
            y = r * self.row_height
            # noinspection PyArgumentList
            for angle in range(0, 360, 60):
                x += math.cos(math.radians(angle)) * self.edge_length
                y += math.sin(math.radians(angle)) * self.edge_length
                yield x + self.edge_length, y

    image = Image.new('RGB', (1500, 1000), 'white')
    draw = Draw(image)
    hexagon_generator = HexagonGenerator(40)
    for n in g.nodes_iter():
        row, col = n
        hexagon = hexagon_generator(row, col)
        draw.polygon(list(hexagon), outline='black', fill='red')

    image.show()


def draw_square_grid(g):
    size = 10

    def node_to_pixel(node):
        return node[0] * (size * 2) + int(size / 2), node[1] * (size * 2) + int(size / 2)

    size = 20
    uni_width = math.sqrt(g.number_of_nodes())
    image = Image.new('RGB', (size * 2 * uni_width, size * 2 * uni_width), 'white')

    draw = Draw(image)
    for e in g.edges_iter():
        src, target = e
        draw.line((node_to_pixel(src), node_to_pixel(target)), fill='blue', width=1)
    for n in g.nodes_iter():
        row, col = n
        draw.ellipse((row * (size * 2), col * (size * 2), row * (size * 2) + size, col * size * 2 + size),
                     outline='black', fill='red')
    image.show()


def draw_hex_circles(g, uni_radius):

    size = 50
    centerx = int(size * uni_radius * 2)
    centery = int(size * uni_radius * 2)

    def node_to_pixel(node):
        x, y = node
        x_offset = 0 if y == 0 else math.fabs(y) * size * (math.fabs(y) / y)
        return x * (size * 2) + int(size / 2) + centerx + x_offset, y * (size * 2) + int(size / 2) + centery

    image = Image.new('RGB', (size * 2 * uni_radius * 2, size * 2 * uni_radius * 2), 'white')

    draw = Draw(image)
    for e in g.edges_iter():
        src, target = e
        draw.line((node_to_pixel(src), node_to_pixel(target)), fill='blue', width=1)
    print("nodes num: {}".format(g.number_of_nodes()))
    for n in g.nodes_iter():
        col, row = n
        col_offset = 0 if row == 0 else math.fabs(row) * size * (math.fabs(row) / row)
        draw.ellipse((col * (size * 2) + centerx + col_offset, row * (size * 2) + centery,
                      col * (size * 2) + size + centerx + col_offset, row * size * 2 + size + centery),
                     outline='black', fill='red')

    for n in g.nodes_iter():
        draw.text(node_to_pixel(n), str(n), fill='black')
    image.show()


uni_size = 35
density = 3.5


uni = gen_hex_center(uni_size)
remove_warps(uni)
draw_hex_circles(uni, uni_size)

#nx.draw_networkx(g, node_size=40)
#pyplot.show()
# draw_networkx(g)
