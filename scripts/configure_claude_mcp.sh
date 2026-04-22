#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=".212"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_BASE="$(conda info --base)"
PYTHON_PATH="${CONDA_BASE}/envs/${ENV_NAME}/bin/python"
SERVER_PATH="${PROJECT_DIR}/src/server.py"
ACCOUNTS_FILE="${PROJECT_DIR}/accounts.json"
ENV_FILE="${PROJECT_DIR}/.env"

if [[ ! -f "${PYTHON_PATH}" ]]; then
  echo "Python executable not found: ${PYTHON_PATH}"
  exit 1
fi

if [[ ! -f "${SERVER_PATH}" ]]; then
  echo "Server file not found: ${SERVER_PATH}"
  exit 1
fi

echo "==> Removing existing local MCP config for trading212 if present"
claude mcp remove trading212 -s local >/dev/null 2>&1 || true

if [[ -f "${ACCOUNTS_FILE}" ]]; then
  echo "==> accounts.json found — registering in multi-account mode"
  claude mcp add trading212 \
    "${PYTHON_PATH}" \
    "${SERVER_PATH}" \
    -s local \
    -e ACCOUNTS_CONFIG="${ACCOUNTS_FILE}"
elif [[ -f "${ENV_FILE}" ]]; then
  echo "==> accounts.json not found — falling back to .env (single-account mode)"
  set -a
  source "${ENV_FILE}"
  set +a

  : "${TRADING212_API_KEY:?Missing TRADING212_API_KEY in .env}"
  : "${TRADING212_API_SECRET:?Missing TRADING212_API_SECRET in .env}"
  : "${ENVIRONMENT:?Missing ENVIRONMENT in .env}"

  claude mcp add trading212 \
    "${PYTHON_PATH}" \
    "${SERVER_PATH}" \
    -s local \
    -e TRADING212_API_KEY="${TRADING212_API_KEY}" \
    -e TRADING212_API_SECRET="${TRADING212_API_SECRET}" \
    -e ENVIRONMENT="${ENVIRONMENT}"
else
  echo "Neither accounts.json nor .env found at ${PROJECT_DIR}."
  echo
  echo "Create one of:"
  echo "  cp accounts.json.example accounts.json   # multi-account (recommended)"
  echo "  cp .env.example .env                     # single-account (legacy)"
  exit 1
fi

echo
echo "==> MCP registration complete"
claude mcp get trading212
