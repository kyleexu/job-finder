"""API 路由"""

import time

from fastapi import APIRouter, HTTPException
from loguru import logger

from ..agents.job_finder_agent import get_job_finder_agent
from ..config import get_settings
from ..logging_setup import preview
from ..models.schemas import ChatRequest, ChatResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    logger.debug("health_check")
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    started = time.perf_counter()
    logger.info(
        "HTTP /api/chat 收到请求 reset_history={} message={}",
        request.reset_history,
        preview(request.message, 400),
    )
    try:
        agent = get_job_finder_agent()
        if request.reset_history:
            logger.info("清空对话历史 history_len={}", len(agent.get_history()))
            agent.clear_history()

        reply = agent.run(request.message)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "HTTP /api/chat 成功 elapsed_ms={:.0f} reply_chars={} reply={}",
            elapsed_ms,
            len(reply),
            preview(reply, 1000),
        )
        return ChatResponse(success=True, reply=reply, agent_name=agent.name)
    except ValueError as exc:
        logger.exception("HTTP /api/chat ValueError elapsed_ms={:.0f}", (time.perf_counter() - started) * 1000)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("HTTP /api/chat 失败 elapsed_ms={:.0f}", (time.perf_counter() - started) * 1000)
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
