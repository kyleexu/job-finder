"""API 路由"""

import re
import time

from fastapi import APIRouter, Header, HTTPException
from loguru import logger

from ..agents.job_finder_agent import get_job_finder_agent
from ..config import get_settings
from ..logging_setup import preview
from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    HealthResponse,
)
from .. import store

router = APIRouter()

_USER_ID_RE = re.compile(r"^[\w.@+-]{1,64}$")


def _require_user_id(x_user_id: str | None) -> str:
    user_id = (x_user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="缺少请求头 X-User-Id")
    if not _USER_ID_RE.match(user_id):
        raise HTTPException(
            status_code=400,
            detail="X-User-Id 仅支持字母数字及 . _ @ + -，最长 64",
        )
    return user_id


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    logger.debug("health_check")
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(x_user_id: str | None = Header(default=None)) -> list[ConversationSummary]:
    user_id = _require_user_id(x_user_id)
    return [
        ConversationSummary(
            id=item.id,
            title=item.title or "新对话",
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in store.list_conversations(user_id=user_id)
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    x_user_id: str | None = Header(default=None),
) -> ConversationDetail:
    user_id = _require_user_id(x_user_id)
    conv = store.get_conversation(conversation_id, user_id=user_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = store.list_messages(conversation_id)
    return ConversationDetail(
        id=conv.id,
        title=conv.title or "新对话",
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[{"role": item.role, "content": item.content} for item in messages],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    x_user_id: str | None = Header(default=None),
) -> dict[str, bool]:
    user_id = _require_user_id(x_user_id)
    if not store.delete_conversation(conversation_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"ok": True}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_user_id: str | None = Header(default=None),
) -> ChatResponse:
    started = time.perf_counter()
    user_id = _require_user_id(x_user_id)
    conversation_id = None if request.reset_history else request.conversation_id
    logger.info(
        "HTTP /api/chat 收到请求 user_id={} conversation_id={} reset_history={} message={}",
        user_id,
        conversation_id,
        request.reset_history,
        preview(request.message, 400),
    )
    try:
        if conversation_id:
            conv = store.get_conversation(conversation_id, user_id=user_id)
            if conv is None:
                raise HTTPException(status_code=404, detail="会话不存在")
        else:
            conv = store.create_conversation(user_id=user_id)
            conversation_id = conv.id

        history = store.list_messages(conversation_id)
        agent = get_job_finder_agent()
        reply = agent.run(request.message, history=history)
        store.append_turn(conversation_id, request.message, reply)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "HTTP /api/chat 成功 user_id={} conversation_id={} elapsed_ms={:.0f} reply_chars={} reply={}",
            user_id,
            conversation_id,
            elapsed_ms,
            len(reply),
            preview(reply, 1000),
        )
        return ChatResponse(
            success=True,
            reply=reply,
            agent_name=agent.name,
            conversation_id=conversation_id,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        logger.exception("HTTP /api/chat ValueError elapsed_ms={:.0f}", (time.perf_counter() - started) * 1000)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("HTTP /api/chat 失败 elapsed_ms={:.0f}", (time.perf_counter() - started) * 1000)
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
