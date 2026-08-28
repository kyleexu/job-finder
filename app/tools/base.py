"""工具定义"""

from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, parameters: str) -> str:
        """执行工具逻辑。"""

    def describe(self) -> str:
        return f"- {self.name}: {self.description}"
