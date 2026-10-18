#!/usr/bin/env bash
# Lanzador del MCP "deepseek-executor" (stdio). Crea el venv local si falta; la clave se lee de <repo>/.env.
set -euo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -x "$AQUI/.venv/bin/python" ]; then
  UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
  "$UV" venv "$AQUI/.venv" --python 3.11 -q
  "$UV" pip install --python "$AQUI/.venv/bin/python" -q "mcp>=1.2,<2" "httpx>=0.27"
fi
export DEEPSEEK_EXECUTOR_ROOT="${DEEPSEEK_EXECUTOR_ROOT:-$(cd "$AQUI/../.." && pwd)}"
exec "$AQUI/.venv/bin/python" "$AQUI/server.py" "$@"
