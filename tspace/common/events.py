from tspace.common.models import (
    SectorPublic,
    TraderShipPublic,
    PlayerPublic,
    GameConfigPublic, CombatantPublic, BattlePublic,
)


class ServerEvents:
    async def on_game_enter(self, player: PlayerPublic, config: GameConfigPublic):
        pass

    async def on_ship_enter_sector(
        self, sector: SectorPublic, ship: TraderShipPublic
    ) -> None:
        pass

    async def on_ship_exit_sector(
        self, sector: SectorPublic, ship: TraderShipPublic
    ) -> None:
        pass

    async def on_battle_enter(self, battle: BattlePublic):
        pass
