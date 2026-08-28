"""工具注册表"""

from typing import Any

from .base import Tool


class ToolRegistry:
    """管理 Agent 可用工具，类似 Java 里的 Service Registry。"""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools)

    def openai_tools(self) -> list[dict[str, Any]]:
        return [tool.openai_schema() for tool in self._tools.values()]
