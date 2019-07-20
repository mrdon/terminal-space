from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tspace.server.constants import PORT_NAMES, PORT_SUFFIXES
from tspace.server.util import AutoIncrementId
from tspace.server.models import Port, PortClass, CommodityType, TradingCommodity

if TYPE_CHECKING:
    from tspace.server.models import Galaxy


def random_port_type(rnd: random.Random) -> PortClass:
    type_chance = rnd.randint(0, 99)
    if type_chance < 20:
        return PortClass.by_id(1)
    elif type_chance < 40:
        return PortClass.by_id(2)
    elif type_chance < 60:
        return PortClass.by_id(3)
    elif type_chance < 70:
        return PortClass.by_id(4)
    elif type_chance < 80:
        return PortClass.by_id(5)
    elif type_chance < 90:
        return PortClass.by_id(6)
    elif type_chance < 95:
        return PortClass.by_id(7)
    else:
        return PortClass.by_id(8)


autoid = AutoIncrementId()


def create(game: Galaxy, sector_id: int) -> Port:
    commodities = []

    ptype = random_port_type(game.rnd)

    for ctype in CommodityType:
        buying = ptype.buying[ctype]
        amount = game.rnd.randint(200, 2000)
        commodities.append(TradingCommodity(ctype, amount, buying))

    name = game.rnd.choice(PORT_NAMES)
    suffix = game.rnd.choice(PORT_SUFFIXES)
    if suffix:
        name = " ".join([name, suffix])
        name = name.strip()
    port = Port(autoid.incr(), sector_id, name, commodities)
    game.ports[port.id] = port
    return port
