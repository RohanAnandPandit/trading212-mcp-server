bootstrap:
	./scripts/bootstrap.sh

configure:
	./scripts/configure_claude_mcp.sh

validate:
	./scripts/validate_setup.sh

run:
	./scripts/run_server.sh

test:
	uv run pytest tests/ -v