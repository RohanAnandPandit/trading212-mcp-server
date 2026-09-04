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

Ensure all new features include appropriate tests. Install the locked runtime
and development dependencies, then run tests using:

```bash
uv sync --frozen
uv run --frozen pytest -q
```

The cache regression suite uses synthetic credentials, temporary directories,
and a mocked HTTP transport. It does not require a Trading212 account or make
live Trading212 requests. GitHub Actions runs it on Python 3.11.

## Cache isolation and synchronization

Keep cache construction in `src/utils/hishel_config.py`. Hishel 0.1.2's default
cache key does not include Authorization; header-based separation depends on
the upstream response declaring `Vary: Authorization`. We cannot rely on that
header. Without our namespace isolation, account B can request the same URL
as account A and receive A's cached balance without contacting the API.

The namespace hashes a JSON pair containing the API base URL and the actual
Authorization header. Using the full header covers both legacy API keys and
Basic key/secret credentials, including secret rotation. The base URL separates
environments and API versions. The new cache root deliberately excludes old
shared entries because their filenames cannot identify the owning account.

Clients for the same namespace must reuse a `FileStorage` instance within the
process. Hishel's file lock belongs to that instance, not the directory. Two
instances pointing at the same directory have independent locks, allowing a
reader to see incomplete JSON during a write. The registry lock covers lookup
and creation together; locking only insertion, or using a memoization helper
that permits concurrent creation, would still allow duplicate instances.
Hishel's own lock then coordinates file reads and writes after the factory
returns. Closing a client is safe for other clients with the currently pinned
Hishel version because `FileStorage.close()` is a no-op; recheck this behavior
when upgrading the dependency.

The registry uses resolved paths so separate working directories stay separate,
and weak references so unused storage instances can be reclaimed. Reclaiming
an instance does not erase its on-disk cache. This is synchronization within a
process, not an interprocess lock or encrypted storage; see the README for
deployment and cache-file access guidance.

Preserve both kinds of regression coverage when changing this code: different
credentials must never reuse responses, and concurrent same-credential clients
must wait for complete writes. The concurrency test pauses a writer after it
flushes partial JSON, starts a second client's read, and verifies that the read
waits until the writer finishes. A separate test starts factory calls together
to check that they all receive the same storage instance.

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
