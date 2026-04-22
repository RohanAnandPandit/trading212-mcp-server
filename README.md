# Trading212 MCP Server

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](CHANGELOG.md)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/1cda5fa3-820c-4e9b-a4ad-4d5c447cd7cd)
[![MCP Badge](https://lobehub.com/badge/mcp/rohananandpandit-trading212-mcp-server?style=plastic)](https://lobehub.com/mcp/rohananandpandit-trading212-mcp-server)

## Overview

The Trading212 MCP server is a [Model Context Protocol](https://modelcontextprotocol.io/introduction) server implementation that provides seamless data connectivity to the Trading212 trading platform enabling advanced interaction capabilities.

## Star History

<a href="https://www.star-history.com/?repos=RohanAnandPandit%2Ftrading212-mcp-server&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=RohanAnandPandit/trading212-mcp-server&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=RohanAnandPandit/trading212-mcp-server&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=RohanAnandPandit/trading212-mcp-server&type=date&legend=top-left" />
 </picture>
</a>

## Core Features

### Trading212 API Integration
- Comprehensive account management:
  - Account metadata retrieval
  - Cash balance monitoring
  - Portfolio management with positions tracking
- Advanced order handling:
  - Market orders
  - Limit orders
  - Stop-limit orders
  - Order history and management
- Portfolio management:
  - Pies (portfolio buckets) management
  - Position tracking and search
  - Historical order data with pagination

### Market Data Access
- Tradeable instruments information
- Exchange data with working schedules
- Historical trading data access
- Real-time market connectivity

### Financial Analysis Tools
- Professional financial analysis capabilities
- Currency-aware data processing
- Comprehensive trading data analysis
- Risk management tools

### MCP Protocol Support
- Full MCP protocol implementation
- Resource-based API endpoints
- Tool-based functionality
- Prompt-based analysis capabilities

## Technical Requirements

- Python >= 3.11 (as specified in .python-version)
- Pydantic >= 2.11.4
- Hishel


## Tools

### Instruments Metadata
- `search_exchange`: Fetch exchanges, optionally filtered by name or ID
- `search_instrument`: Fetch instruments, optionally filtered by ticker or name

### Pies
- `fetch_pies`: Fetch all pies
- `duplicate_pie`: Duplicate a pie
- `create_pie`: Create a new pie
- `update_pie`: Update a specific pie by ID
- `delete_pie`: Delete a pie

The Trading 212 `Pies` API is still operational, but the latest public
`api.json` marks it as deprecated upstream.

### Equity Orders
- `fetch_all_orders`: Fetch all equity orders
- `place_limit_order`: Place a limit order
- `place_market_order`: Place a market order
- `place_stop_order`: Place a stop order
- `place_stop_limit_order`: Place a stop-limit order
- `cancel_order`: Cancel an existing order by ID
- `fetch_order`: Fetch a specific order by ID

### Account Data
- `fetch_account_summary`: Fetch account summary
- `fetch_account_cash`: Fetch account cash balance
- `fetch_account_info`: Deprecated alias for `fetch_account_summary`


### Personal Portfolio
- `fetch_positions`: Fetch open positions, optionally filtered by ticker
- `fetch_position_by_ticker`: Fetch a single open position by ticker
- `fetch_all_open_positions`: Fetch all open positions
- `fetch_open_position_by_ticker`: Deprecated alias for `fetch_position_by_ticker`
- `search_specific_position_by_ticker`: Deprecated alias for `fetch_position_by_ticker`

### Historical items
- `fetch_historical_order_data`: Fetch historical order data with pagination
- `fetch_paid_out_dividends`: Fetch historical dividend data with pagination
- `fetch_exports_list`: Lists detailed information about all csv account exports
- `request_csv_export`: Request a CSV export of the account's orders, dividends and transactions history
- `fetch_transaction_list`: Fetch superficial information about movements to and from your account

## Resources

### Account Resources
- `trading212://account/summary`
- `trading212://account/cash`
- `trading212://positions`
- `trading212://positions/{ticker}`
- `trading212://account/info` deprecated alias for `trading212://account/summary`
- `trading212://account/portfolio` deprecated alias for `trading212://positions`
- `trading212://account/positions` compatibility alias for `trading212://positions`
- `trading212://account/portfolio/{ticker}` deprecated alias for `trading212://positions/{ticker}`
- `trading212://account/positions/{ticker}` compatibility alias for `trading212://positions/{ticker}`

### Order Resources
- `trading212://orders`
- `trading212://orders/{order_id}`

### Portfolio Resources
- `trading212://pies`
- `trading212://pies/{pie_id}`

### Market Resources
- `trading212://instruments`
- `trading212://exchanges`

### Reports Resources
- `trading212://history/exports`

## Prompts

### Data Analysis
- `analyse_trading212_data`: Analyse trading212 data with currency context

The prompt includes:
- Professional financial expertise
- Currency-aware analysis
- Cautious financial advice
- Dynamic currency information from account data

## Installation

### Clone repository
```bash
git clone https://github.com/RohanAnandPandit/trading212-mcp-server.git
```

### Environment Configuration
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Using Claude Desktop

#### Installing via Docker

- Clone the repository and build a local image to be utilized by your Claude desktop client

```sh
cd trading212-mcp-server
docker build -t mcp/trading212-mcp-server .
```

- Change your `claude_desktop_config.json` to match the following, replacing `REPLACE_API_KEY` with your actual key:
- `TRADING212_API_SECRET` is optional. If supplied, the server will use the
  newer Basic auth flow from the current public `api.json`; if omitted, it
  will continue using the legacy API-key-only header that Trading 212 still
  exposes for compatibility.

 > `claude_desktop_config.json` path
 >
 > - On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
 > - On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "trading212": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "-e",
        "TRADING212_API_KEY",
        "mcp/trading212-mcp-server"
      ],
      "env": {
        "TRADING212_API_KEY": "REPLACE_API_KEY",
        "TRADING212_API_SECRET": "OPTIONAL_API_SECRET"
      }
    }
  }
}
```

### Using uv

```json
{
 "mcpServers": {
  "trading212": {
    "command": "uv",
    "args": [
        "run",
        "--directory",
        "<insert path to repo>",
        "src/server.py"
    ],
    "env": {
        "TRADING212_API_KEY": "<insert api key>",
        "TRADING212_API_SECRET": "<optional api secret>"
    }
  }
 }
}
```

### Generating API credentials
- You can generate the API key from your account settings
- Visit the [Trading212 help centre](https://helpcentre.trading212.com/hc/en-us/articles/14584770928157-How-can-I-generate-an-API-key) for more information
- If you are using the API key for the "Practice" account in Trading212 then set the `ENVIRONMENT` to `demo` in `.env`
- Set `ENVIRONMENT` to `live` if you are using the API key for real money
- `docs/api.json` is the canonical checked-in copy of the latest public Trading 212 API schema used for this project


### Install packages

```
uv install
```

or 

```
pip install -r requirements.txt
```

#### Running

After connecting Claude client with the MCP tool via json file and installing the packages, Claude should see the server's mcp tools:

You can run the server yourself via:
In trading212-mcp-server repo: 
```
uv run src/server.py
```

#### Using MCP Inspector

The `mcp[cli]` dependency in this project includes the `mcp dev` command,
which starts your server and launches the MCP Inspector via
`@modelcontextprotocol/inspector`.

Prerequisites:
- Node.js and `npx` installed locally
- Project dependencies installed with `uv` or `pip`
- `TRADING212_API_KEY` configured in `.env`
- Optional: `TRADING212_API_SECRET` if you want to test the newer Basic auth flow

From the repository root, run:

```bash
uv run mcp dev src/server.py
```

If you are using the repo's virtual environment directly, this works too:

```bash
./.venv/bin/mcp dev src/server.py
```

The inspector command will:
- start the Trading 212 MCP server using this repo's Python environment
- open or print the MCP Inspector session details
- let you call tools and inspect resources interactively before wiring the server into a desktop client

If the inspector fails to start, the most common cause is that `npx` is not
available on your `PATH`. Installing Node.js usually resolves that.

### Using Python

```json
{
 "mcpServers": {
  "trading212": {
    "command": "<insert path to python>",
    "args": [
        "<insert path to repo>/src/server.py"
    ]
  }
 }
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
- Open an issue in the GitHub repository

## Documentation

For the Trading212 API documentation, view the [Public API docs](https://docs.trading212.com/api).


## Legal Notice

This is an unofficial implementation of the Trading212 MCP protocol. Always consult official Trading212 documentation and terms of service before using this software.

## Credits

- Project maintained by [Rohan Pandit](https://github.com/RohanAnandPandit)

## Contributing
- Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for more information on how to contribute to this project.
