#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

# 用 python -m pip，避免 .venv/bin/pip shebang 指错导致装不上
if ! "$PYTHON" -c "import fastapi, uvicorn, openai, httpx, loguru, pydantic_settings" 2>/dev/null; then
  echo "缺少依赖，正在安装 requirements.txt ..."
  "$PYTHON" -m pip install -r "$ROOT/requirements.txt"
fi

echo "启动 Job Finder"
echo "  目录: $ROOT"
echo "  地址: http://127.0.0.1:8001"
echo "  日志: $ROOT/run.log"
echo "  Python: $PYTHON"
exec "$PYTHON" run.py
