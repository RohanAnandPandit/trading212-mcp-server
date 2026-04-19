#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
CLIENT_FILE="${PROJECT_DIR}/src/utils/client.py"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo ".env file not found"
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${TRADING212_API_KEY:?Missing TRADING212_API_KEY in .env}"
: "${TRADING212_API_SECRET:?Missing TRADING212_API_SECRET in .env}"
: "${ENVIRONMENT:?Missing ENVIRONMENT in .env}"

AUTH=$(printf '%s:%s' "${TRADING212_API_KEY}" "${TRADING212_API_SECRET}" | base64)

echo "==> Testing Trading212 direct API access"
curl -sS -i "https://${ENVIRONMENT}.trading212.com/api/v0/equity/account/cash" \
  -H "Authorization: Basic ${AUTH}" \
  | sed -n '1,20p'

echo
echo "==> Testing Python client"
python "${CLIENT_FILE}"

echo
echo "==> Testing Claude MCP registration"
claude mcp get trading212