"""API 数据模型"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入")
    conversation_id: str | None = Field(default=None, description="会话 ID，空则新建")
    reset_history: bool = Field(
        default=False,
        description="兼容旧客户端：true 时新建会话，忽略 conversation_id",
    )


class ChatResponse(BaseModel):
    success: bool
    reply: str
    agent_name: str
    conversation_id: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationDetail(ConversationSummary):
    messages: list[dict[str, str]]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
