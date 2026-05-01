from abc import ABC, abstractmethod


class BaseSkill(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, action: str, params: dict, user_id: int) -> str:
        pass
