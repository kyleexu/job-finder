"""FastAPI 入口"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from loguru import logger

from .agents.job_finder_agent import shutdown_job_finder_agent
from .config import get_settings
from .logging_setup import setup_logging
from .routes.chat import router

settings = get_settings()
log_file = setup_logging(settings.log_level)
_INDEX_HTML = Path(__file__).resolve().parent.parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info(
        "Job Finder 启动 name={} version={} host={} port={} llm_model={} llm_base={} jsearch_base={} jsearch_key_set={} log_file={}",
        settings.app_name,
        settings.app_version,
        settings.host,
        settings.port,
        settings.llm_model_id,
        settings.llm_base_url,
        settings.jsearch_base_url,
        bool(settings.jsearch_api_key),
        log_file,
    )
    yield
    logger.info("Job Finder 关闭，清理 Agent 缓存")
    shutdown_job_finder_agent()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Job Finder: LLM + tools + FastAPI",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(_INDEX_HTML)
