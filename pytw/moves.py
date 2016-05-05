class ShipMoves:

    def __init__(self, player, galaxy):
        super().__init__()
        self.galaxy = galaxy
        self.player = player

    def move_sector(self, ship_id, target_sector_id):
        target = self.galaxy.sectors[target_sector_id]
        ship = self.galaxy.ships[ship_id]
        ship_sector = self.galaxy.sectors[ship.sector_id]

        if ship.player_id != self.player.player_id:
            raise ValueError("Ship not occupied by player")

        if not ship_sector.can_warp(target.sector_id):
            raise ValueError("Target sector not adjacent to ship")

        ship_sector.exit_ship(ship)
        target.enter_ship(ship)
        ship.move_sector(target.sector_id)
        self.player.visit_sector(target.sector_id)
