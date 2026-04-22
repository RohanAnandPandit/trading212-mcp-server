#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=".212"
PYTHON_VERSION="3.11"

echo "==> Creating conda environment: ${ENV_NAME}"
source "$(conda info --base)/etc/profile.d/conda.sh"
if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "Conda environment ${ENV_NAME} already exists"
else
  conda create -n "${ENV_NAME}" python="${PYTHON_VERSION}" -y
fi

echo "==> Activating conda environment: ${ENV_NAME}"
conda activate "${ENV_NAME}"

echo "==> Installing uv"
python -m pip install --upgrade pip
pip install uv

echo "==> Installing project dependencies"
if [[ -f requirements.txt ]]; then
  uv pip install -r requirements.txt
else
  echo "requirements.txt not found"
  exit 1
fi

echo "==> Bootstrap complete"
echo
echo "Next steps — pick ONE configuration path:"
echo
echo "  Multi-account (recommended):"
echo "    1. cp accounts.json.example accounts.json"
echo "    2. Edit accounts.json — add one entry per Trading212 account"
echo
echo "  Single-account (legacy, backward-compatible):"
echo "    1. cp .env.example .env"
echo "    2. Fill in Trading212 credentials in .env"
echo
echo "Then:"
echo "  3. Run: ./scripts/configure_claude_mcp.sh"
echo "  4. Run: ./scripts/validate_setup.sh"