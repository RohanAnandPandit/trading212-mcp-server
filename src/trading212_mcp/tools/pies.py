from collections.abc import Callable
from datetime import datetime

from mcp.server import MCPServer

from ..client import Trading212Client
from ..models.pies import (
    AccountBucketInstrumentsDetailedResponse,
    AccountBucketResultResponse,
    DividendCashActionEnum,
    DuplicateBucketRequest,
    PieRequest,
)
from ..registration import annotations, safe_handler


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.tool("fetch_pies", annotations=annotations(write=False))
    @safe_handler
    def fetch_pies() -> list[AccountBucketResultResponse]:
        """Fetch all pies."""
        return get_client().get_pies()

    @mcp.tool("create_pie", annotations=annotations(write=True))
    @safe_handler
    def create_pie(
        name: str,
        instrument_shares: dict[str, float],
        dividend_cash_action: DividendCashActionEnum | None = None,
        end_date: datetime | None = None,
        goal: float | None = None,
        icon: str | None = None,
    ) -> AccountBucketInstrumentsDetailedResponse:
        """
        Create a new pie with the specified parameters.

        Args:
            name: Name of the pie
            instrument_shares: Dictionary mapping instrument tickers to their
            weights in the pie
                (e.g., {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5})
            dividend_cash_action: How dividends are handled. Defaults to REINVEST.
                Possible values: REINVEST, TO_ACCOUNT_CASH
            end_date: Optional end date for the pie in ISO 8601 format
                (e.g., '2024-12-31T23:59:59Z')
            goal: Total desired value of the pie in account currency
            icon: Optional icon identifier for the pie

        Returns:
            AccountBucketInstrumentsDetailedResponse: Details of the created pie
        """
        pie_data = PieRequest(
            name=name,
            instrumentShares=instrument_shares,
            dividendCashAction=dividend_cash_action,
            endDate=end_date,
            goal=goal,
            icon=icon,
        )
        return get_client().create_pie(pie_data)

    @mcp.tool("delete_pie", annotations=annotations(write=True))
    @safe_handler
    def delete_pie(pie_id: int) -> None:
        """Delete a pie."""
        return get_client().delete_pie(pie_id)

    @mcp.tool("fetch_a_pie", annotations=annotations(write=False))
    @safe_handler
    def fetch_a_pie(pie_id: int) -> AccountBucketInstrumentsDetailedResponse:
        """Fetch a specific pie by ID."""
        return get_client().get_pie_by_id(pie_id)

    @mcp.tool("update_pie", annotations=annotations(write=True))
    @safe_handler
    def update_pie(
        pie_id: int,
        name: str,
        instrument_shares: dict[str, float] | None = None,
        dividend_cash_action: DividendCashActionEnum | None = None,
        end_date: datetime | None = None,
        goal: float | None = None,
        icon: str | None = None,
    ) -> AccountBucketInstrumentsDetailedResponse:
        """
        Update an existing pie with new parameters. The pie must be renamed when
        updating it.

        Args:
            pie_id: ID of the pie to update
            name: New name for the pie. Required when updating a pie.
            instrument_shares: Dictionary mapping instrument tickers to their new
            weights in the pie
                (e.g., {'AAPL_US_EQ': 0.5, 'MSFT_US_EQ': 0.5})
            dividend_cash_action: How dividends should be handled.
                Possible values: REINVEST, TO_ACCOUNT_CASH
            end_date: New end date for the pie in ISO 8601 format
                (e.g., '2024-12-31T23:59:59Z')
            goal: New total desired value of the pie in account currency
            icon: New icon identifier for the pie

        Returns:
            AccountBucketInstrumentsDetailedResponse: Updated details of the pie
        """
        pie_data = PieRequest(
            name=name,
            instrumentShares=instrument_shares,
            dividendCashAction=dividend_cash_action,
            endDate=end_date,
            goal=goal,
            icon=icon,
        )
        return get_client().update_pie(pie_id, pie_data)

    @mcp.tool("duplicate_pie", annotations=annotations(write=True))
    @safe_handler
    def duplicate_pie(
        pie_id: int,
        name: str | None = None,
        icon: str | None = None,
    ) -> AccountBucketInstrumentsDetailedResponse:
        """
        Create a duplicate of an existing pie.

        Args:
            pie_id: ID of the pie to duplicate
            name: Optional new name for the duplicated pie
            icon: Optional new icon for the duplicated pie

        Returns:
            AccountBucketInstrumentsDetailedResponse: Details of the duplicated pie
        """
        duplicate_request = DuplicateBucketRequest(name=name, icon=icon)
        return get_client().duplicate_pie(pie_id, duplicate_request)
