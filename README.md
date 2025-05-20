# Trading212 MCP Server

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](CHANGELOG.md)

## Overview

The Trading212 MCP (Model Context Protocol) Server is a high-performance, scalable server implementation that provides real-time market data connectivity for Trading212's trading platform. This server acts as a bridge between the Trading212 platform and various market data providers, enabling seamless data flow and efficient trading operations.

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



## Installation


### Environment Configuration
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Install packages

```
uv install -e .
```

### Generating API key
- See https://helpcentre.trading212.com/hc/en-us/articles/14584770928157-How-can-I-generate-an-API-key

#### Running

After connecting Claude client with the MCP tool via json file and installing the packages, Claude should see the server's mcp tools:

You can run the server yourself via:
In trading212-mcp-server repo: 
```
uv run src/server.py
```

## Tools

### Account Management
- `get_account_info`: Fetch account metadata
- `get_account_cash`: Fetch account cash balance
- `get_account_positions`: Fetch all open positions
- `get_account_position_by_ticker`: Fetch a position by ticker (deprecated)
- `search_position_by_ticker`: Search for a position by ticker using POST endpoint

### Order Management
- `get_orders`: Fetch current orders
- `get_history_orders`: Fetch historical order data with pagination
- `place_market_order`: Place a market order
- `place_limit_order`: Place a limit order
- `place_stop_limit_order`: Place a stop-limit order
- `cancel_order`: Cancel an existing order

### Portfolio Management
- `get_pies`: Fetch all pies
- `duplicate_pie`: Duplicate a pie
- `delete_pie`: Delete a pie

### Market Data
- `get_instruments`: Fetch all tradeable instruments
- `get_exchanges`: Fetch all exchanges and their working schedules

### Reports
- `get_reports`: Get account export reports

## Resources

### Account Resources
- `trading212://account/info`: Fetch account metadata
- `trading212://account/cash`: Fetch account cash balance
- `trading212://account/portfolio`: Fetch all open positions
- `trading212://account/portfolio/{ticker}`: Fetch an open position by ticker

### Order Resources
- `trading212://orders`: Fetch current orders
- `trading212://orders/{order_id}`: Fetch a specific order by ID

### Portfolio Resources
- `trading212://pies`: Fetch all pies
- `trading212://pies/{pie_id}`: Fetch a specific pie by ID

### Market Resources
- `trading212://instruments`: Fetch all tradeable instruments
- `trading212://exchanges`: Fetch all exchanges and their working schedules

### Reports Resources
- `trading212://history/exports`: Get account export reports

## Prompts

### Data Analysis
- `analyse_trading212_data`: Analyse trading212 data with currency context

The prompt includes:
- Professional financial expertise
- Currency-aware analysis
- Cautious financial advice
- Dynamic currency information from account data

## Installation

### Using Claude Desktop

#### Installing via Docker

- Clone the repository and build a local image to be utilized by your Claude desktop client

```sh
cd trading212-mcp-server
docker build -t mcp/trading212-mcp-server .
```

- Change your `claude_desktop_config.json` to match the following, replacing `REPLACE_API_KEY` with your actual key:

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
        "mcp/trading212"
      ],
      "env": {
        "TRADING212_API_KEY": "REPLACE_API_KEY"
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
        "TRADING212_API_KEY": "<insert api key>"
    }
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

For the Trading212 API documentation, visit https://t212public-api-docs.redoc.ly/.


## Legal Notice

This is an unofficial implementation of the Trading212 MCP protocol. Always consult official Trading212 documentation and terms of service before using this software.

## Credits

- Project maintained by [Rohan Pandit](https://github.com/RohanAnandPandit)

## Contributing
- Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for more information on how to contribute to this project.
