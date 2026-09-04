from collections.abc import Callable

from mcp.server import MCPServer

from ..client import Trading212Client
from ..models.metadata import Exchange, TradeableInstrument
from ..registration import annotations, safe_handler


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.tool("search_instrument", annotations=annotations(write=False))
    @safe_handler
    def search_instrument(search_term: str | None = None) -> list[TradeableInstrument]:
        """
        Fetch instruments, optionally filtered by ticker or name.

        Args:
            search_term: Search term to filter instruments by ticker or name
            (case-insensitive)

        Returns:
            List of matching TradeableInstrument objects, or all instruments if no
            search term is provided
        """
        instruments = get_client().get_instruments()

        if not search_term:
            return instruments

        search_lower = search_term.lower()
        return [
            inst
            for inst in instruments
            if (inst.ticker and search_lower in inst.ticker.lower())
            or (inst.name and search_lower in inst.name.lower())
        ]

    @mcp.tool("search_exchange", annotations=annotations(write=False))
    @safe_handler
    def search_exchange(search_term: str | None = None) -> list[Exchange]:
        """
        Fetch exchanges, optionally filtered by name or ID.

        Args:
            search_term: Optional search term to filter exchanges by name or ID
            (case-insensitive)

        Returns:
            List of matching Exchange objects, or all exchanges if no search term
            is provided
        """
        exchanges = get_client().get_exchanges()

        if not search_term:
            return exchanges

        search_lower = search_term.lower()
        return [
            exch
            for exch in exchanges
            if (exch.name and search_lower in exch.name.lower())
            or (str(exch.id) == search_term)
        ]
