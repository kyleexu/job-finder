"""OpenAI 兼容 LLM 客户端（DeepSeek Chat Completions + Tool Calls）。"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator, Sequence
from typing import Any

from loguru import logger
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

from .message import Message

ChatMessage = Message | ChatCompletionMessage | dict[str, Any]


class LLMClient:
    """封装 OpenAI Chat Completions API。"""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ):
        self.model = model or os.getenv("LLM_MODEL_ID", "deepseek-v4-flash")
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("LLM_API_KEY 或 OPENAI_API_KEY 未配置")

        logger.info("LLMClient 初始化 model={} base_url={}", self.model, self.base_url)
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatCompletionMessage:
        payload = [_to_api_message(message) for message in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": payload,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        roles = [
            getattr(item, "role", None) or (item.get("role") if isinstance(item, dict) else type(item).__name__)
            for item in payload
        ]
        tool_names = [item.get("function", {}).get("name") for item in (tools or [])]
        logger.info(
            "LLM chat 请求 model={} messages={} roles={} tools={} temp={} max_tokens={}",
            self.model,
            len(payload),
            roles,
            tool_names,
            self.temperature,
            self.max_tokens,
        )
        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception:
            logger.exception(
                "LLM chat 失败 elapsed_ms={:.0f} model={}",
                (time.perf_counter() - started) * 1000,
                self.model,
            )
            raise

        choice = response.choices[0]
        message = choice.message
        elapsed_ms = (time.perf_counter() - started) * 1000
        tool_calls_dump = []
        if message.tool_calls:
            for call in message.tool_calls:
                tool_calls_dump.append(
                    {
                        "id": call.id,
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    }
                )
        logger.info(
            "LLM chat 完整返回 elapsed_ms={:.0f} finish_reason={} id={} usage={}\ncontent:\n{}\ntool_calls:\n{}",
            elapsed_ms,
            choice.finish_reason,
            getattr(response, "id", None),
            getattr(response, "usage", None),
            message.content or "",
            json.dumps(tool_calls_dump, ensure_ascii=False, indent=2) if tool_calls_dump else "[]",
        )
        return message

    def stream(self, messages: Sequence[ChatMessage]) -> Iterator[str]:
        payload = [_to_api_message(message) for message in messages]
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=payload,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


def _to_api_message(message: ChatMessage) -> dict[str, Any] | ChatCompletionMessage:
    if isinstance(message, ChatCompletionMessage):
        return message
    if isinstance(message, Message):
        return {"role": message.role, "content": message.content}
    return message
