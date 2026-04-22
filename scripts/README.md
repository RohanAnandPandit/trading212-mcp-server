# Trading212 MCP Server Setup

This fork contains a patched Trading212 client that uses API key + API secret with HTTP Basic auth.

## Prerequisites

- Conda installed
- Claude Code installed and available as `claude`
- One or more Trading212 API key/secret pairs (one per account you want to query)

# Trading212 MCP Server Setup

This fork contains a patched Trading212 client that uses API key + API secret with HTTP Basic auth.

---

## 🚀 Quick Start (Recommended)

### macOS / Linux

The server supports two configuration paths. Pick one — the scripts auto-detect which you used.

**Multi-account (recommended):** configure any number of Trading212 accounts in `accounts.json` and query them individually, in subsets, or all at once via the `account` parameter on each tool.

```bash
git clone <your-fork-url>
cd trading212-mcp-server

make bootstrap
cp accounts.json.example accounts.json
# 👉 Edit accounts.json — one entry per account; set "default" to the account
#    used when a tool is called without an explicit account param

make configure
make validate

claude
```

**Single-account (legacy, backward-compatible):** if `accounts.json` is absent, the server falls back to `.env` and behaves identically to the pre-multi-account version.

```bash
git clone <your-fork-url>
cd trading212-mcp-server

make bootstrap
cp .env.example .env
# 👉 Edit .env and add TRADING212_API_KEY, TRADING212_API_SECRET, ENVIRONMENT

make configure
make validate

claude
```

#### accounts.json format

```json
{
  "default": "my_account",
  "accounts": [
    {"name": "my_account",   "api_key": "...", "api_secret": "...", "environment": "live"},
    {"name": "demo_account", "api_key": "...", "api_secret": "...", "environment": "demo"}
  ]
}
```

- `name` — unique identifier referenced by the `account` tool parameter (case-sensitive)
- `environment` — `"live"` or `"demo"`
- `default` — account used when a read tool is called with `account=None`

`accounts.json` is gitignored; credentials never land in the repo. See `accounts.json.example` for the template.

#### What the scripts do

| Script | Behaviour |
|---|---|
| `scripts/bootstrap.sh` | Create conda env `.212`, install dependencies |
| `scripts/configure_claude_mcp.sh` | Register the MCP server with Claude. If `accounts.json` exists, passes `ACCOUNTS_CONFIG` to the MCP; otherwise sources `.env` and passes `TRADING212_API_KEY`/`TRADING212_API_SECRET`/`ENVIRONMENT`. |
| `scripts/validate_setup.sh` | If `accounts.json` exists, validates every configured account against the Trading212 API. Otherwise validates the single `.env` credentials. Then checks the Claude MCP registration. |
| `scripts/run_server.sh` | Activate the conda env and launch the server directly (useful for local debugging). Works in both modes. |

### Windows (PowerShell)

> **Prerequisites:** Conda installed and initialised for PowerShell (`conda init powershell`), Claude Code available as `claude`.

```powershell
git clone <your-fork-url>
cd trading212-mcp-server

# 1. Create the conda env and install dependencies
.\scripts\windows\bootstrap.ps1

# 2. Copy and edit the env file
copy .env.example .env
# 👉 Open .env and add your API key + secret

# 3. Register the MCP server with Claude
.\scripts\windows\configure_claude_mcp.ps1

# 4. Validate the setup
.\scripts\windows\validate_setup.ps1

# 5. Launch Claude Code
claude
```

If PowerShell blocks script execution, run this once in an elevated shell:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

#### Windows script reference

| Script | Purpose |
|---|---|
| `scripts\windows\bootstrap.ps1` | Create conda env, install Python deps |
| `scripts\windows\configure_claude_mcp.ps1` | Register MCP server with Claude Code |
| `scripts\windows\run_server.ps1` | Run the MCP server directly |
| `scripts\windows\validate_setup.ps1` | Test API access, Python client, and MCP registration |