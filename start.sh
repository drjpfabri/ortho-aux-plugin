#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v docker >/dev/null 2>&1; then
  docker compose up --build -d
  echo
  echo "Ortho Aux iniciado."
  echo "Docs:    http://127.0.0.1:8000/docs"
  echo "OpenAPI: http://127.0.0.1:8000/openapi.json"
  echo "Health:  http://127.0.0.1:8000/health"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Docker ou Python 3 é necessário."
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
mkdir -p data
export ORTHO_AUX_DB="$(pwd)/data/ortho_aux.sqlite3"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
