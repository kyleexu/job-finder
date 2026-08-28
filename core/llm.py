"""OpenAI 兼容 LLM 客户端"""

import os
from collections.abc import Iterator

from openai import OpenAI

from .message import Message


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

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, messages: list[Message]) -> str:
        payload = [{"role": message.role, "content": message.content} for message in messages]
        response = self._client.chat.completions.create(
            model=self.model,
            messages=payload,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""

    def stream(self, messages: list[Message]) -> Iterator[str]:
        payload = [{"role": message.role, "content": message.content} for message in messages]
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
