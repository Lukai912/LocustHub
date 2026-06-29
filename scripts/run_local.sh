#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt

if [ ! -d frontend/node_modules ]; then
  npm install --prefix frontend --registry=https://registry.npmjs.org/
fi

(
  cd frontend
  VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api/v1}" \
  VITE_DEMO_TOKEN="${DEMO_TOKEN:-dev-token}" \
  npm run build
)

(
  cd backend
  echo "LocustHub Admin: http://127.0.0.1:8000/"
  echo "LocustHub Swagger: http://127.0.0.1:8000/docs"
  FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-../frontend/dist}" \
  PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
)
