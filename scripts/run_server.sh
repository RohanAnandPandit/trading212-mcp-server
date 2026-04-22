#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=".212"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  source "${ENV_FILE}"
  set +a
fi

cd "${PROJECT_DIR}"
python src/server.py