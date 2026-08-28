"""工具定义（OpenAI / DeepSeek function calling）。"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    @abstractmethod
    def run(self, arguments: dict[str, Any]) -> str:
        """执行工具逻辑。"""

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
