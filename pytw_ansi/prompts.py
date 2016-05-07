from enum import Enum


class PromptType(Enum):
    SECTOR = 1
    PORT = 2


class PromptTransition(Exception):

    def __init__(self, next_prompt: PromptType):
        self.next = next_prompt
