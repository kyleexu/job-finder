#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "启动 Job Finder"
echo "  目录: $ROOT"
echo "  地址: http://127.0.0.1:8001"
echo "  日志: $ROOT/run.log"
echo "  Python: $PYTHON"
exec "$PYTHON" run.py
