"""Account-aware analysis prompt."""

import logging
from collections.abc import Callable

from mcp.server import MCPServer
from pydantic import ValidationError

from .client import Trading212Client
from .errors import Trading212Error

logger = logging.getLogger(__name__)
PROMPT = """Analyse the user's Trading 212 data carefully. Distinguish observed
account data from assumptions, and describe limitations of any financial analysis.
Use the account currency if the instrument currency is not supplied.
GBX represents pence: 100 GBX equals 1 GBP.
"""


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.prompt("analyse_trading212_data")
    def analyse_trading212_data_prompt() -> str:
        """Analyse trading212 data."""
        try:
            summary = get_client().get_account_summary()
        except (Trading212Error, ValidationError):
            logger.warning("Account currency unavailable for analysis prompt")
            return PROMPT
        return PROMPT + (f"\nCurrency: {summary.currency}" if summary.currency else "")
