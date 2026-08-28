"""对话消息模型"""

from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str
