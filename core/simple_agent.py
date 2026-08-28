"""带工具调用的 SimpleAgent"""

import re

from app.tools.registry import ToolRegistry

from .agent import Agent
from .llm import LLMClient
from .message import Message

TOOL_CALL_PATTERN = re.compile(r"\[TOOL_CALL:([^:]+):([^\]]+)\]")


class SimpleAgent(Agent):
    """LLM + 可选工具调用的最小 Agent 实现。"""

    def __init__(
        self,
        name: str,
        llm: LLMClient,
        system_prompt: str | None = None,
        tool_registry: ToolRegistry | None = None,
        max_tool_rounds: int = 5,
    ):
        super().__init__(name, llm, system_prompt)
        self.tool_registry = tool_registry
        self.max_tool_rounds = max_tool_rounds

    def _build_system_prompt(self) -> str:
        base_prompt = self.system_prompt or "You are a helpful assistant."
        if not self.tool_registry:
            return base_prompt

        tools_description = self.tool_registry.describe_tools()
        return (
            f"{base_prompt}\n\n"
            "## Available tools\n"
            f"{tools_description}\n\n"
            "## Tool call format\n"
            "When you need a tool, use:\n"
            "`[TOOL_CALL:tool_name:key=value,...]`\n"
            "Example: `[TOOL_CALL:get_transport_tip:topic=S-Bahn]`"
        )

    def _parse_tool_calls(self, text: str) -> list[dict[str, str]]:
        return [
            {"tool_name": tool_name.strip(), "parameters": parameters.strip()}
            for tool_name, parameters in TOOL_CALL_PATTERN.findall(text)
        ]

    def _execute_tool(self, tool_name: str, parameters: str) -> str:
        if not self.tool_registry:
            return "No tools configured."

        tool = self.tool_registry.get(tool_name)
        if tool is None:
            return f"Unknown tool: {tool_name}"

        return tool.run(parameters)

    def run(self, user_input: str) -> str:
        messages = [Message(role="system", content=self._build_system_prompt())]
        messages.extend(self._history)
        messages.append(Message(role="user", content=user_input))

        final_answer = ""

        for _ in range(self.max_tool_rounds):
            assistant_text = self.llm.chat(messages)
            messages.append(Message(role="assistant", content=assistant_text))

            tool_calls = self._parse_tool_calls(assistant_text)
            if not tool_calls:
                final_answer = assistant_text
                break

            tool_results: list[str] = []
            for call in tool_calls:
                result = self._execute_tool(call["tool_name"], call["parameters"])
                tool_results.append(f"[{call['tool_name']}] {result}")

            tool_message = "Tool results:\n" + "\n".join(tool_results)
            messages.append(Message(role="user", content=tool_message))
        else:
            final_answer = messages[-1].content

        self.add_message(Message(role="user", content=user_input))
        self.add_message(Message(role="assistant", content=final_answer))
        return final_answer
