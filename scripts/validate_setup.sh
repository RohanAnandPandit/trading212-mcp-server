#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACCOUNTS_FILE="${PROJECT_DIR}/accounts.json"
ENV_FILE="${PROJECT_DIR}/.env"
CLIENT_FILE="${PROJECT_DIR}/src/utils/client.py"

test_api() {
  local env="$1" key="$2" secret="$3" label="$4"
  local auth
  auth=$(printf '%s:%s' "${key}" "${secret}" | base64)
  echo "==> [${label}] GET https://${env}.trading212.com/api/v0/equity/account/cash"
  curl -sS -o /dev/null -w "    HTTP %{http_code}\n" \
    "https://${env}.trading212.com/api/v0/equity/account/cash" \
    -H "Authorization: Basic ${auth}"
}

if [[ -f "${ACCOUNTS_FILE}" ]]; then
  echo "==> Validating accounts.json"
  python - "${ACCOUNTS_FILE}" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    cfg = json.load(f)
for key in ("default", "accounts"):
    if key not in cfg:
        print(f"ERROR: missing required key '{key}'")
        sys.exit(1)
names = [a["name"] for a in cfg["accounts"]]
if cfg["default"] not in names:
    print(f"ERROR: default '{cfg['default']}' not in accounts {names}")
    sys.exit(1)
print(f"    default: {cfg['default']}")
print(f"    accounts: {names}")
PY

  echo
  echo "==> Testing each configured account against Trading212 API"
  while IFS=$'\t' read -r name env key secret; do
    test_api "${env}" "${key}" "${secret}" "${name}"
  done < <(python - "${ACCOUNTS_FILE}" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    cfg = json.load(f)
for a in cfg["accounts"]:
    print(f"{a['name']}\t{a['environment']}\t{a['api_key']}\t{a['api_secret']}")
PY
)
elif [[ -f "${ENV_FILE}" ]]; then
  echo "==> accounts.json not found — validating single-account .env"
  set -a
  source "${ENV_FILE}"
  set +a

  : "${TRADING212_API_KEY:?Missing TRADING212_API_KEY in .env}"
  : "${TRADING212_API_SECRET:?Missing TRADING212_API_SECRET in .env}"
  : "${ENVIRONMENT:?Missing ENVIRONMENT in .env}"

  test_api "${ENVIRONMENT}" "${TRADING212_API_KEY}" "${TRADING212_API_SECRET}" "default"

  echo
  echo "==> Testing Python client"
  python "${CLIENT_FILE}"
else
  echo "Neither accounts.json nor .env found at ${PROJECT_DIR}."
  exit 1
fi

echo
echo "==> Testing Claude MCP registration"
claude mcp get trading212
