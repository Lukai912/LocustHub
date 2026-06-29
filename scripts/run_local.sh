#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt

if [ ! -d frontend/node_modules ]; then
  npm install --prefix frontend --registry=https://registry.npmjs.org/
fi

cleanup() {
  kill "${api_pid}" "${admin_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd backend
  PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
api_pid=$!

(
  cd frontend
  VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:8000/api/v1}" \
  VITE_DEMO_TOKEN="${DEMO_TOKEN:-dev-token}" \
  npm run dev -- --host 127.0.0.1
) &
admin_pid=$!

echo "LocustHub API: http://127.0.0.1:8000/docs"
echo "LocustHub Admin: http://127.0.0.1:5173"
wait -n "${api_pid}" "${admin_pid}"
