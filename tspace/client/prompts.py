from enum import Enum


class PromptType(Enum):
    SECTOR = 1
    PORT = 2
    QUIT = 3
    NONE = 4
    BATTLE = 5


class PromptTransition(Exception):
    def __init__(self, next_prompt: PromptType):
        self.next = next_prompt
