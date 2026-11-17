from collections.abc import Callable

from mcp.server import MCPServer

from ..client import Trading212Client
from ..models.metadata import Exchange, TradeableInstrument
from ..registration import annotations, safe_handler

DEFAULT_INSTRUMENT_LIMIT = 100
MAX_INSTRUMENT_LIMIT = 5000


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.tool("search_instrument", annotations=annotations(write=False))
    @safe_handler
    def search_instrument(
        search_term: str | None = None,
        limit: int = DEFAULT_INSTRUMENT_LIMIT,
    ) -> list[TradeableInstrument]:
        """
        Search tradeable instruments by ticker or name (case-insensitive).

        Exact ticker matches come first, then ticker prefixes, then other
        matches. The full instrument list has thousands of entries, so results
        are capped; refine search_term rather than raising the limit.

        Args:
            search_term: Text to find in the ticker or name; omit to list
                instruments without filtering
            limit: Maximum results to return, 1-5000 (default 100)

        Returns:
            Up to `limit` matching TradeableInstrument objects
        """
        limit = min(MAX_INSTRUMENT_LIMIT, max(1, limit))
        instruments = get_client().get_instruments()

        if not search_term:
            return instruments[:limit]

        term = search_term.lower()

        def rank(inst: TradeableInstrument) -> int | None:
            ticker = (inst.ticker or "").lower()
            name = (inst.name or "").lower()
            # Tickers carry a market suffix (AAPL_US_EQ): match the symbol too.
            if term in (ticker, ticker.split("_", 1)[0], name):
                return 0
            if ticker.startswith(term):
                return 1
            if term in ticker or term in name:
                return 2
            return None

        ranked = [(r, inst) for inst in instruments if (r := rank(inst)) is not None]
        ranked.sort(key=lambda pair: pair[0])  # stable: keeps upstream order
        return [inst for _, inst in ranked[:limit]]

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
