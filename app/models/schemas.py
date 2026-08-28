"""API 数据模型"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入")
    reset_history: bool = Field(default=False, description="是否清空对话历史")


class ChatResponse(BaseModel):
    success: bool
    reply: str
    agent_name: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
