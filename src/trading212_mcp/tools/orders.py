from collections.abc import Callable

from mcp.server import MCPServer

from ..client import Trading212Client
from ..models.orders import (
    LimitRequest,
    LimitRequestTimeValidityEnum,
    MarketRequest,
    Order,
    Price,
    Quantity,
    StopLimitRequest,
    StopLimitRequestTimeValidityEnum,
    StopRequest,
    StopRequestTimeValidityEnum,
    Ticker,
)
from ..registration import annotations, safe_handler


def register(mcp: MCPServer, get_client: Callable[[], Trading212Client]) -> None:
    @mcp.tool("fetch_all_orders", annotations=annotations(write=False))
    @safe_handler
    def fetch_orders() -> list[Order]:
        """Fetch all equity orders."""
        return get_client().get_orders()

    @mcp.tool("place_limit_order", annotations=annotations(write=True))
    @safe_handler
    def place_limit_order(
        ticker: Ticker,
        quantity: Quantity,
        limit_price: Price,
        time_validity: LimitRequestTimeValidityEnum = LimitRequestTimeValidityEnum.DAY,
    ) -> Order:
        """
        Place a limit order to buy or sell an instrument at a specified price or better.

        Args:
            ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
            quantity: Number of shares/units; positive buys, negative sells
            limit_price: Limit price for the order
            time_validity: Time validity of the order. Defaults to DAY.
                Possible values: DAY, GOOD_TILL_CANCEL

        Returns:
            Order: Details of the placed order
        """
        limit_request = LimitRequest(
            ticker=ticker,
            quantity=quantity,
            limitPrice=limit_price,
            timeValidity=time_validity,
        )
        return get_client().place_limit_order(limit_request)

    @mcp.tool("place_market_order", annotations=annotations(write=True))
    @safe_handler
    def place_market_order(
        ticker: Ticker,
        quantity: Quantity,
        extended_hours: bool = False,
    ) -> Order:
        """
        Place a market order to buy or sell an instrument at the current market price.

        Args:
            ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
            quantity: Number of shares/units; positive buys, negative sells
            extended_hours: Whether the order can execute outside regular trading
                hours when the instrument supports it

        Returns:
            Order: Details of the placed order
        """
        market_request = MarketRequest(
            ticker=ticker, quantity=quantity, extendedHours=extended_hours
        )
        return get_client().place_market_order(market_request)

    @mcp.tool("place_stop_order", annotations=annotations(write=True))
    @safe_handler
    def place_stop_order(
        ticker: Ticker,
        quantity: Quantity,
        stop_price: Price,
        time_validity: StopRequestTimeValidityEnum = StopRequestTimeValidityEnum.DAY,
    ) -> Order:
        """
        Place a stop order to buy or sell an instrument when the market price
        reaches a specified stop price.

        Args:
            ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
            quantity: Number of shares/units; positive buys, negative sells
            stop_price: Stop price that triggers the order
            time_validity: Time validity of the order. Defaults to DAY.
                Possible values: DAY, GOOD_TILL_CANCEL

        Returns:
            Order: Details of the placed order
        """
        stop_request = StopRequest(
            ticker=ticker,
            quantity=quantity,
            stopPrice=stop_price,
            timeValidity=time_validity,
        )
        return get_client().place_stop_order(stop_request)

    @mcp.tool("place_stop_limit_order", annotations=annotations(write=True))
    @safe_handler
    def place_stop_limit_order(
        ticker: Ticker,
        quantity: Quantity,
        stop_price: Price,
        limit_price: Price,
        time_validity: StopLimitRequestTimeValidityEnum = StopLimitRequestTimeValidityEnum.DAY,
    ) -> Order:
        """
        Place a stop-limit order to buy or sell an instrument when the market
        price reaches a specified stop price, then execute at a specified limit
        price or better.

        Args:
            ticker: Ticker symbol of the instrument to trade (e.g., 'AAPL_US_EQ')
            quantity: Number of shares/units; positive buys, negative sells
            stop_price: Stop price that triggers the limit order
            limit_price: Limit price for the order
            time_validity: Time validity of the order. Defaults to DAY.
                Possible values: DAY, GOOD_TILL_CANCEL

        Returns:
            Order: Details of the placed order
        """
        stop_limit_request = StopLimitRequest(
            ticker=ticker,
            quantity=quantity,
            stopPrice=stop_price,
            limitPrice=limit_price,
            timeValidity=time_validity,
        )
        return get_client().place_stop_limit_order(stop_limit_request)

    @mcp.tool("cancel_order", annotations=annotations(write=True))
    @safe_handler
    def cancel_order_by_id(order_id: int) -> None:
        """Cancel an existing order."""
        return get_client().cancel_order(order_id)

    @mcp.tool("fetch_order", annotations=annotations(write=False))
    @safe_handler
    def fetch_order_by_id(order_id: int) -> Order:
        """Fetch a specific order by ID."""
        return get_client().get_order_by_id(order_id)
