"""SQLite 会话存储：conversations + messages（正文为文本/JSON 字符串）。"""

from __future__ import annotations

import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from core.message import Message

from .config import get_settings

_LOCK = threading.Lock()
_CONN: sqlite3.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'local',
    title TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, id);
"""


@dataclass
class Conversation:
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def db_path() -> Path:
    settings = get_settings()
    path = Path(settings.sqlite_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    return path


def init_db() -> Path:
    global _CONN
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        if _CONN is None:
            _CONN = sqlite3.connect(path, check_same_thread=False)
            _CONN.row_factory = sqlite3.Row
            _CONN.execute("PRAGMA foreign_keys = ON")
            _CONN.execute("PRAGMA journal_mode = WAL")
            _CONN.executescript(_SCHEMA)
            _CONN.commit()
    logger.info("SQLite 已就绪 path={}", path)
    return path


def _conn() -> sqlite3.Connection:
    if _CONN is None:
        init_db()
    assert _CONN is not None
    return _CONN


def _title_from(text: str) -> str:
    line = " ".join(text.strip().split())
    if not line:
        return "新对话"
    if len(line) > 36:
        return line[:36] + "…"
    return line


def create_conversation(*, user_id: str = "local", title: str = "") -> Conversation:
    conv_id = str(uuid.uuid4())
    ts = _now()
    with _LOCK:
        _conn().execute(
            "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, user_id, title, ts, ts),
        )
        _conn().commit()
    logger.info("创建会话 id={} user_id={}", conv_id, user_id)
    return Conversation(id=conv_id, user_id=user_id, title=title, created_at=ts, updated_at=ts)


def get_conversation(conversation_id: str, *, user_id: str | None = None) -> Conversation | None:
    with _LOCK:
        if user_id is None:
            row = _conn().execute(
                "SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
        else:
            row = _conn().execute(
                """
                SELECT id, user_id, title, created_at, updated_at
                FROM conversations WHERE id = ? AND user_id = ?
                """,
                (conversation_id, user_id),
            ).fetchone()
    if row is None:
        return None
    return Conversation(**dict(row))


def list_conversations(*, user_id: str) -> list[Conversation]:
    with _LOCK:
        rows = _conn().execute(
            """
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [Conversation(**dict(row)) for row in rows]


def delete_conversation(conversation_id: str, *, user_id: str) -> bool:
    with _LOCK:
        cur = _conn().execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        _conn().commit()
    logger.info("删除会话 id={} user_id={} deleted={}", conversation_id, user_id, cur.rowcount)
    return cur.rowcount > 0


def list_messages(conversation_id: str) -> list[Message]:
    with _LOCK:
        rows = _conn().execute(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
    return [Message(role=row["role"], content=row["content"]) for row in rows]


def append_turn(conversation_id: str, user_text: str, assistant_text: str) -> None:
    ts = _now()
    with _LOCK:
        conn = _conn()
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (conversation_id, user_text, ts),
        )
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
            (conversation_id, assistant_text, ts),
        )
        conv = conn.execute(
            "SELECT title FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        title = conv["title"] if conv else ""
        if not title:
            title = _title_from(user_text)
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, ts, conversation_id),
        )
        conn.commit()
    logger.info("写入会话回合 conversation_id={} user_chars={} assistant_chars={}", conversation_id, len(user_text), len(assistant_text))
