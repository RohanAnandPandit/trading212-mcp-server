from collections.abc import Callable

from mcp.server import MCPServer

from ..client import Trading212Client
from ..models.history import (
    EnqueuedReportResponse,
    PaginatedResponseHistoricalOrder,
    PaginatedResponseHistoryDividendItem,
    PaginatedResponseHistoryTransactionItem,
    ReportDataIncluded,
    ReportResponse,
)
from ..registration import annotations, safe_handler


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.tool("fetch_historical_order_data", annotations=annotations(write=False))
    @safe_handler
    def fetch_historical_order_data(
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoricalOrder:
        """Fetch historical order data with pagination."""
        return get_client().get_historical_order_data(
            cursor=cursor, ticker=ticker, limit=limit
        )

    @mcp.tool("fetch_paid_out_dividends", annotations=annotations(write=False))
    @safe_handler
    def fetch_paid_out_dividends(
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoryDividendItem:
        """Fetch historical dividend data with pagination."""
        return get_client().get_dividends(cursor=cursor, ticker=ticker, limit=limit)

    @mcp.tool("fetch_exports_list", annotations=annotations(write=False))
    @safe_handler
    def fetch_exports_list() -> list[ReportResponse]:
        """Lists detailed information about all csv account exports."""
        return get_client().get_reports()

    @mcp.tool("request_csv_export", annotations=annotations(write=True))
    @safe_handler
    def request_csv_export(
        include_dividends: bool = True,
        include_interest: bool = True,
        include_orders: bool = True,
        include_transactions: bool = True,
        time_from: str | None = None,
        time_to: str | None = None,
    ) -> EnqueuedReportResponse:
        """
        Request a CSV export of the account's orders, dividends and transactions
        history.
        Once the export is complete it can be accessed from the download link in the
         exports list.

        Args:
            include_dividends: Whether to include dividend information in the export.
                Defaults to True
            include_interest: Whether to include interest information in the export.
            Defaults to True
            include_orders: Whether to include order history in the export.
            Defaults to True
            include_transactions: Whether to include transaction history in the export.
            Defaults to True
            time_from: Start time for the report in ISO 8601 format
            (e.g., '2023-01-01T00:00:00Z')
            time_to: End time for the report in ISO 8601 format
            (e.g., '2023-12-31T23:59:59Z')

        Returns:
            EnqueuedReportResponse: Response containing the report ID and status
        """
        data_included = ReportDataIncluded(
            includeDividends=include_dividends,
            includeInterest=include_interest,
            includeOrders=include_orders,
            includeTransactions=include_transactions,
        )
        return get_client().request_export(
            data_included=data_included, time_from=time_from, time_to=time_to
        )

    @mcp.tool("fetch_transaction_list", annotations=annotations(write=False))
    @safe_handler
    def fetch_transaction_list(
        cursor: str | None = None,
        time: str | None = None,
        limit: int = 20,
    ) -> PaginatedResponseHistoryTransactionItem:
        """Fetch superficial information about movements to and from your
        account."""
        return get_client().get_history_transactions(
            cursor=cursor, time_from=time, limit=limit
        )
