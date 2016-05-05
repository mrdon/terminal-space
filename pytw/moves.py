import json

from pytw.planet import Galaxy, Player, Sector, Ship


class PlayerPublic:
    def __init__(self, player: Player):
        self.id = player.player_id
        self.name = player.name
        self.ship = ShipPublic(player.ship, player.sector)
        self.visited = list(player.visited_sectors.keys())


class ShipPublic:
    def __init__(self, ship: Ship, sector: Sector):
        self.id = ship.ship_id
        self.name = ship.name
        self.type = ship.ship_type
        self.sector = SectorPublic(sector)


class SectorPublic:
    def __init__(self, sector: Sector):
        self.id = sector.sector_id
        self.coords = sector.coords
        self.warps = sector.warps
        self.traders = None  # todo
        self.ships = None  # todo


class Events:
    def on_game_enter(self, player: PlayerPublic):
        pass

    def on_new_sector(self, sector: SectorPublic):
        pass

    def on_invalid_action(self, error: str):
        pass


class EventLogger:
    def __init__(self, obj):
        self.obj = obj
        self.callable_results = []

    def __getattr__(self, attr):
        ret = getattr(self.obj, attr)
        if hasattr(ret, "__call__"):
            return self.FunctionWrapper(self, ret)
        return ret

    class FunctionWrapper:
        def __init__(self, parent, callable):
            self.parent = parent
            self.callable = callable

            class MyEncoder(json.JSONEncoder):
                def default(self, o):
                    return {k: v for k, v in o.__dict__.items() if v is not None}
            self.encoder = MyEncoder()

        def __call__(self, *args, **kwargs):
            print('Calling {} with args: {}'.format(self.callable.__name__, [self.encoder.encode(a) for a in args]))
            ret = self.callable(*args, **kwargs)
            return ret


class Actions:

    def __init__(self, player: Player, game: Galaxy, events: Events):
        self.__player = player
        self.__game = game
        self.__moves = ShipMoves(player, game, EventLogger(events))

    def move(self, target_id):
        print("move: {}".format(target_id))
        ship_id = self.__player.ship_id
        self.__moves.move_sector(ship_id, target_id)


class ShipMoves:

    def __init__(self, player, galaxy: Galaxy, events: Events):
        super().__init__()
        self.galaxy = galaxy
        self.player = player
        self.events = events
        self.events.on_game_enter(PlayerPublic(player))

    def move_sector(self, ship_id, target_sector_id):
        target = self.galaxy.sectors[target_sector_id]
        ship = self.galaxy.ships[ship_id]
        ship_sector = self.galaxy.sectors[ship.sector_id]

        if ship.player_id != self.player.player_id:
            self.events.on_invalid_action("Ship not occupied by player")
            return

        if not ship_sector.can_warp(target.sector_id):
            self.events.on_invalid_action("Target sector not adjacent to ship")
            return

        ship_sector.exit_ship(ship)
        target.enter_ship(ship)
        ship.move_sector(target.sector_id)
        self.player.visit_sector(target.sector_id)
        self.events.on_new_sector(SectorPublic(target))
