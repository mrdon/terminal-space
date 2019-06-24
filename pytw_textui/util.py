from typing import Iterable
from typing import Sequence
from typing import Tuple


def frag_join(sep: Tuple[str, str], seq: Iterable[Tuple[str, str]]) -> Sequence[
    Tuple[str, str]]:

    first = True
    for frag in seq:
        if not first:
            yield sep
        else:
            first = False
        yield frag
