"""Compatibility launcher and MCP Inspector entry point."""

from trading212_mcp.server import create_server, main

mcp = create_server()

if __name__ == "__main__":
    main()
