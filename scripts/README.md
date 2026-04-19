# Trading212 MCP Server Setup

This fork contains a patched Trading212 client that uses API key + API secret with HTTP Basic auth.

## Prerequisites

- Conda installed
- Claude Code installed and available as `claude`
- A Trading212 API key and secret

# Trading212 MCP Server Setup

This fork contains a patched Trading212 client that uses API key + API secret with HTTP Basic auth.

---

## 🚀 Quick Start (Recommended)

### macOS / Linux

Run everything using `make`:

```bash
git clone <your-fork-url>
cd trading212-mcp-server

make bootstrap
cp .env.example .env
# 👉 Now edit .env and add your API key + secret

make configure
make validate

claude
```

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