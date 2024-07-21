from tspace.common.models import SectorPublic, PlayerPublic, PortPublic, BattlePublic


class SectorActions:
    async def move_trader(self, sector_id: int) -> SectorPublic:
        pass

    async def enter_port(self, port_id: int) -> tuple[PlayerPublic, PortPublic]:
        pass

    async def enter_battle(self, attacker_ship_id: int, target_ship_id: int) -> BattlePublic:
        pass


class PortActions:
    async def buy_from_port(
        self, port_id: int, commodity: str, amount: int
    ) -> tuple[PlayerPublic, PortPublic]:
        pass

    async def sell_to_port(
        self, port_id: int, commodity: str, amount: int
    ) -> tuple[PlayerPublic, PortPublic]:
        pass

    async def exit_port(self, port_id: int) -> PlayerPublic:
        pass


class BattleActions:
    async def exit_battle(self, battle_id: int) -> PlayerPublic:
        pass
