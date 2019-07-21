from dataclasses import dataclass
from typing import Any, Tuple, List, Callable

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.widgets import Frame

from tspace.client.ui.dynamic_label import DynamicLabel


@dataclass
class Stat:
    title: str
    callable: Callable[[], Any]
    multiline: bool = False


class StatFrame(Frame):
    def __init__(
        self, title, condition: Callable[[], bool], stats: List[Stat], **kwargs
    ):
        self.condition = condition
        self.stats = stats
        Frame.__init__(self, title=title, body=DynamicLabel(self.get_label), **kwargs)

    def get_label(self):
        render_values = self.condition()
        fragments = []
        max_length = max(len(stat.title) for stat in self.stats if not stat.multiline)
        for stat in self.stats:
            pad = " " * (max_length - len(stat.title))
            fragments.append(("grey", f"{stat.title}: {pad}"))

            value = stat.callable() if render_values else ""
            if isinstance(value, (list, set)):
                fragments.append(("", "\n"))
                value = "\n".join(f" - {part}" for part in value)
                fragments.append(("bold", value))
            else:
                fragments.append(("bold", str(value)))
            fragments.append(("", "\n"))
        return FormattedText(fragments)
