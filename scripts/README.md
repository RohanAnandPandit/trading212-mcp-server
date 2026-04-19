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