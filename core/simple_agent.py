"""带 DeepSeek Tool Calls 的 SimpleAgent。"""

from __future__ import annotations

import json
import time
from typing import Any

from loguru import logger
from openai.types.chat import ChatCompletionMessage

from app.logging_setup import preview
from app.tools.registry import ToolRegistry

from .agent import Agent
from .llm import LLMClient
from .message import Message


class SimpleAgent(Agent):
    """LLM + OpenAI/DeepSeek function calling。"""

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

    def run(self, user_input: str) -> str:
        started = time.perf_counter()
        logger.info(
            "Agent[{}] 开始 user_input={} history_turns={}",
            self.name,
            preview(user_input, 400),
            len(self._history),
        )
        messages: list[Any] = [
            {"role": "system", "content": self.system_prompt or "You are a helpful assistant."},
        ]
        messages.extend(self._history)
        messages.append({"role": "user", "content": user_input})

        tools = self.tool_registry.openai_tools() if self.tool_registry else None
        logger.info(
            "Agent[{}] 上下文 messages={} tools={}",
            self.name,
            len(messages),
            [item["function"]["name"] for item in tools] if tools else [],
        )
        final_answer = ""

        for round_idx in range(self.max_tool_rounds):
            logger.info("Agent[{}] LLM 第 {}/{} 轮", self.name, round_idx + 1, self.max_tool_rounds)
            message = self.llm.chat(messages, tools=tools)
            messages.append(message)

            if not message.tool_calls:
                final_answer = message.content or ""
                logger.info(
                    "Agent[{}] 本轮无 tool_calls，结束 round={} answer_chars={}",
                    self.name,
                    round_idx + 1,
                    len(final_answer),
                )
                break

            logger.info(
                "Agent[{}] 本轮 tool_calls={} names={}",
                self.name,
                len(message.tool_calls),
                [call.function.name for call in message.tool_calls],
            )
            for tool_call in message.tool_calls:
                result = self._execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                logger.info(
                    "Agent[{}] 回传 tool 结果 name={} tool_call_id={} result={}",
                    self.name,
                    tool_call.function.name,
                    tool_call.id,
                    preview(result, 800),
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
        else:
            last = messages[-1]
            if isinstance(last, ChatCompletionMessage):
                final_answer = last.content or ""
            elif isinstance(last, dict):
                final_answer = str(last.get("content") or "")
            else:
                final_answer = getattr(last, "content", "") or ""
            logger.warning(
                "Agent[{}] 达到 max_tool_rounds={} 强制结束 answer={}",
                self.name,
                self.max_tool_rounds,
                preview(final_answer, 400),
            )

        self.add_message(Message(role="user", content=user_input))
        self.add_message(Message(role="assistant", content=final_answer))
        logger.info(
            "Agent[{}] 完成 elapsed_ms={:.0f} history_turns={} final={}",
            self.name,
            (time.perf_counter() - started) * 1000,
            len(self._history),
            preview(final_answer, 800),
        )
        return final_answer

    def _execute_tool(self, tool_name: str, arguments_json: str) -> str:
        logger.info("Agent 执行工具 name={} arguments={}", tool_name, preview(arguments_json, 800))
        if not self.tool_registry:
            logger.error("Agent 无 tool_registry")
            return "No tools configured."

        tool = self.tool_registry.get(tool_name)
        if tool is None:
            logger.error("未知工具 name={} known={}", tool_name, self.tool_registry.names())
            return f"Unknown tool: {tool_name}"

        try:
            arguments = json.loads(arguments_json or "{}")
        except json.JSONDecodeError as exc:
            logger.exception("工具参数 JSON 解析失败 name={} raw={}", tool_name, preview(arguments_json))
            return f"Invalid tool arguments JSON: {exc}"
        if not isinstance(arguments, dict):
            logger.error("工具参数不是 object name={} type={}", tool_name, type(arguments).__name__)
            return "Tool arguments must be a JSON object."
        started = time.perf_counter()
        try:
            result = tool.run(arguments)
        except Exception:
            logger.exception("工具执行异常 name={} elapsed_ms={:.0f}", tool_name, (time.perf_counter() - started) * 1000)
            raise
        logger.info(
            "工具执行完成 name={} elapsed_ms={:.0f} result_chars={}",
            tool_name,
            (time.perf_counter() - started) * 1000,
            len(result),
        )
        return result
