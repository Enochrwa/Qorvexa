#!/usr/bin/env bash
# Regenerate frontend/src/types/api.d.ts from the backend's OpenAPI schema (no server needed).
set -euo pipefail
cd "$(dirname "$0")/.."
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
(cd backend && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), sort_keys=True))") > "$tmp"
(cd frontend && npx openapi-typescript "$tmp" -o src/types/api.d.ts >/dev/null && npx prettier --write src/types/api.d.ts >/dev/null)
echo "updated frontend/src/types/api.d.ts"
