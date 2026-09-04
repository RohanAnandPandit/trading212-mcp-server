from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, Field

from .base import ApiModel, RequestModel
from .metadata import Instrument


def nonzero(value: float) -> float:
    if value == 0:
        raise ValueError("Quantity must not be zero")
    return value


Quantity = Annotated[float, Field(allow_inf_nan=False), AfterValidator(nonzero)]
Ticker = Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z0-9_.-]+$")]
Price = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class LimitRequestTimeValidityEnum(StrEnum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class OrderStatusEnum(StrEnum):
    LOCAL = "LOCAL"
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    NEW = "NEW"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    REPLACING = "REPLACING"
    REPLACED = "REPLACED"


class OrderStrategyEnum(StrEnum):
    QUANTITY = "QUANTITY"
    VALUE = "VALUE"


class OrderTypeEnum(StrEnum):
    LIMIT = "LIMIT"
    STOP = "STOP"
    MARKET = "MARKET"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSideEnum(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class PositionInitiatedFromEnum(StrEnum):
    API = "API"
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"
    SYSTEM = "SYSTEM"
    AUTOINVEST = "AUTOINVEST"


class StopLimitRequestTimeValidityEnum(StrEnum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class StopRequestTimeValidityEnum(StrEnum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class TimeValidityEnum(StrEnum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class LimitRequest(RequestModel):
    limitPrice: Price
    quantity: Quantity
    ticker: Ticker
    timeValidity: LimitRequestTimeValidityEnum


class MarketRequest(RequestModel):
    extendedHours: bool = False
    quantity: Quantity
    ticker: Ticker


class Order(ApiModel):
    createdAt: datetime | None = None
    currency: str | None = None
    extendedHours: bool | None = None
    filledQuantity: float | None = None
    filledValue: float | None = None
    id: int | None = None
    initiatedFrom: PositionInitiatedFromEnum | None = None
    instrument: Instrument | None = None
    limitPrice: float | None = None
    quantity: float | None = None
    side: OrderSideEnum | None = None
    status: OrderStatusEnum | None = None
    stopPrice: float | None = None
    strategy: OrderStrategyEnum | None = None
    ticker: str | None = None
    timeInForce: TimeValidityEnum | None = None
    type: OrderTypeEnum | None = None
    value: float | None = None


class PlaceOrderError(ApiModel):
    clarification: str | None = None
    code: str | None = None


class StopLimitRequest(RequestModel):
    limitPrice: Price
    quantity: Quantity
    stopPrice: Price
    ticker: Ticker
    timeValidity: StopLimitRequestTimeValidityEnum


class StopRequest(RequestModel):
    quantity: Quantity
    stopPrice: Price
    ticker: Ticker
    timeValidity: StopRequestTimeValidityEnum
