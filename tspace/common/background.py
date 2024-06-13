import asyncio
from typing import Awaitable


class BackgroundTasks:
    background_tasks = set()

    def schedule(self, result: Awaitable) -> None:
        task = asyncio.create_task(result)

        # Add task to the set. This creates a strong reference.
        self.background_tasks.add(task)

        # To prevent keeping references to finished tasks forever,
        # make each task remove its own reference from the set after
        # completion:
        task.add_done_callback(self.background_tasks.discard)


_background_tasks = BackgroundTasks()


def schedule_background_task(result: Awaitable) -> None:
    _background_tasks.schedule(result)
