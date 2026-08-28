"""API 路由"""

from fastapi import APIRouter, HTTPException

from ..agents.job_finder_agent import get_job_finder_agent
from ..config import get_settings
from ..models.schemas import ChatRequest, ChatResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        agent = get_job_finder_agent()
        if request.reset_history:
            agent.clear_history()

        reply = agent.run(request.message)
        return ChatResponse(success=True, reply=reply, agent_name=agent.name)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
