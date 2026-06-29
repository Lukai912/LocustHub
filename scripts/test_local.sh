#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt

node frontend/tests/structure.test.mjs
(
  cd frontend
  npm install --registry=https://registry.npmjs.org/
  npm run build
)
(
  cd backend
  DATABASE_PATH=/private/tmp/locusthub-test-local.db \
  ARTIFACT_ROOT=/private/tmp/locusthub-test-local-artifacts \
  PYTHONPATH=. pytest -q
)
python3 scripts/verify_deployment_package.py
.venv/bin/python -m compileall backend/app scripts/migrate_mysql.py scripts/verify_deployment_package.py
