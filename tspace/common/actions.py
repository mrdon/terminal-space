from tspace.common.models import SectorPublic, PlayerPublic, PortPublic


class SectorActions:
    async def move_trader(self, sector_id: int) -> SectorPublic:
        pass

    async def enter_port(self, port_id: int) -> tuple[PlayerPublic, PortPublic]:
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
