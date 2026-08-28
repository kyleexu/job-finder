"""统一日志：终端 + 项目根目录 log 文件。"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = _PROJECT_ROOT / "run.log"
_CONFIGURED = False

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)
_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} | {message}"
)


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(exception=record.exc_info).log(level, record.getMessage())


def setup_logging(level: str = "INFO") -> Path:
    global _CONFIGURED
    if not _CONFIGURED:
        logger.remove()
        logger.add(
            sys.stderr,
            level=level.upper(),
            colorize=True,
            backtrace=False,
            diagnose=False,
            format=_CONSOLE_FORMAT,
        )
        logger.add(
            LOG_FILE,
            level=level.upper(),
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=False,
            format=_FILE_FORMAT,
        )
        logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
        _CONFIGURED = True
    logger.info("日志文件: {}", LOG_FILE)
    return LOG_FILE


def preview(value: Any, limit: int = 800) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, default=str)
    else:
        text = str(value)
    text = text.replace("\n", "\\n")
    if len(text) > limit:
        return text[:limit] + f"…(+{len(text) - limit} chars)"
    return text


def mask_secret(value: str, keep: int = 4) -> str:
    if not value:
        return "(empty)"
    if len(value) <= keep * 2:
        return "***"
    return f"{value[:keep]}…{value[-keep:]}"
