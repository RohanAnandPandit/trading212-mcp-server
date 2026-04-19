#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=".212"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_BASE="$(conda info --base)"
PYTHON_PATH="${CONDA_BASE}/envs/${ENV_NAME}/bin/python"
SERVER_PATH="${PROJECT_DIR}/src/server.py"
ENV_FILE="${PROJECT_DIR}/.env"

if [[ ! -f "${PYTHON_PATH}" ]]; then
  echo "Python executable not found: ${PYTHON_PATH}"
  exit 1
fi

if [[ ! -f "${SERVER_PATH}" ]]; then
  echo "Server file not found: ${SERVER_PATH}"
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo ".env file not found at ${ENV_FILE}"
  echo "Create it first: cp .env.example .env"
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${TRADING212_API_KEY:?Missing TRADING212_API_KEY in .env}"
: "${TRADING212_API_SECRET:?Missing TRADING212_API_SECRET in .env}"
: "${ENVIRONMENT:?Missing ENVIRONMENT in .env}"

echo "==> Removing existing local MCP config for trading212 if present"
claude mcp remove trading212 -s local >/dev/null 2>&1 || true

echo "==> Adding Trading212 MCP server to Claude"
claude mcp add trading212 \
  "${PYTHON_PATH}" \
  "${SERVER_PATH}" \
  -s local \
  -e TRADING212_API_KEY="${TRADING212_API_KEY}" \
  -e TRADING212_API_SECRET="${TRADING212_API_SECRET}" \
  -e ENVIRONMENT="${ENVIRONMENT}"

echo
echo "==> MCP registration complete"
claude mcp get trading212