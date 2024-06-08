from typing import Callable

from prompt_toolkit import widgets
from prompt_toolkit.application import get_app

from tspace.client.logging import log


class Button(widgets.Button):
    def __init__(
        self,
        text: str,
        handler: Callable[[], None] | None = None,
        disabled: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(text, handler=self._handler, **kwargs)
        self._disabled = disabled
        self._handler = handler

        def get_style() -> str:
            if self._disabled:
                return "class:button.disabled"

            if get_app().layout.has_focus(self):
                return "class:button.focused"
            else:
                return "class:button"

        self.window.style = get_style

    def _handler(self):
        if not self._disabled and self._handler:
            self._handler()

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, value):
        if self._disabled == value:
            return

        self._disabled = value
