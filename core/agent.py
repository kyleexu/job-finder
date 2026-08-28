"""Agent 基类"""

from abc import ABC, abstractmethod

from .llm import LLMClient
from .message import Message


class Agent(ABC):
    """Agent 抽象基类，类似 Java 里的 interface + 部分 default 行为。"""

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: str | None = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self._history: list[Message] = []

    @abstractmethod
    def run(self, user_input: str) -> str:
        """执行一轮或多轮 Agent 逻辑。"""

    def add_message(self, message: Message) -> None:
        self._history.append(message)

    def clear_history(self) -> None:
        self._history.clear()

    def get_history(self) -> list[Message]:
        return self._history.copy()
