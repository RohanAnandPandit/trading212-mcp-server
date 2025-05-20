# Contributing to Trading212 MCP Server

## Getting Started

This project follows the MCP (Model Context Protocol) specification and uses the official MCP Python SDK. Before contributing, please familiarise yourself with the MCP Python SDK documentation:

- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [Core Concepts](https://github.com/modelcontextprotocol/python-sdk#core-concepts)
- [Running Your Server](https://github.com/modelcontextprotocol/python-sdk#running-your-server)

## Core Concepts

### Server Implementation

This project implements a FastMCP server that handles:
- Connection management
- Protocol compliance
- Message routing
- Session management

### Resource Design

When adding new resources:
1. Use the `@mcp.resource` decorator
2. Follow REST-like naming conventions
3. Keep computations minimal
4. Avoid side effects

Example:
```python
@mcp.resource("trading212://account/{ticker}")
def get_account_position(ticker: str) -> Position:
    """Fetch position for a specific ticker."""
    return client.get_position(ticker)
```

### Tool Implementation

When adding new tools:
1. Use the `@mcp.tool` decorator
2. Include proper type hints
3. Add clear docstrings
4. Handle side effects appropriately

Example:
```python
@mcp.tool()
def place_market_order(order: MarketOrder) -> Order:
    """Place a market order with specified parameters."""
    return client.place_order(order)
```

### Prompt Development

When adding new prompts:
1. Use the `@mcp.prompt` decorator
2. Provide clear instructions
3. Include proper context
4. Handle errors gracefully

Example:
```python
@mcp.prompt()
def analyze_trading_data(data: str) -> str:
    """Analyze trading data and provide insights."""
    return f"Analysis of {data}..."
```

## Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a Pull Request

## Testing

Ensure all new features include appropriate tests. Run tests using:

```bash
poetry run pytest
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Include docstrings
- Keep lines under 80 characters

## Security

If you find a security issue, please:
1. Do not open a public issue
2. Email the maintainers directly
3. Follow responsible disclosure practices

## Support

For support, please:
- Check the documentation
- Search existing issues
- Open a new issue if needed
- Join the MCP community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.