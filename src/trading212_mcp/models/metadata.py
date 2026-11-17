from datetime import datetime
from enum import StrEnum

from .base import ApiModel, OpenEnum


class TimeEventTypeEnum(StrEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    BREAK_START = "BREAK_START"
    BREAK_END = "BREAK_END"
    PRE_MARKET_OPEN = "PRE_MARKET_OPEN"
    AFTER_HOURS_OPEN = "AFTER_HOURS_OPEN"
    AFTER_HOURS_CLOSE = "AFTER_HOURS_CLOSE"
    OVERNIGHT_OPEN = "OVERNIGHT_OPEN"


class TradeableInstrumentTypeEnum(StrEnum):
    CRYPTOCURRENCY = "CRYPTOCURRENCY"
    ETF = "ETF"
    FOREX = "FOREX"
    FUTURES = "FUTURES"
    INDEX = "INDEX"
    STOCK = "STOCK"
    WARRANT = "WARRANT"
    CRYPTO = "CRYPTO"
    CVR = "CVR"
    CORPACT = "CORPACT"


class TimeEvent(ApiModel):
    date: datetime | None = None
    type: OpenEnum[TimeEventTypeEnum] | None = None


class WorkingSchedule(ApiModel):
    id: int | None = None
    timeEvents: list[TimeEvent] | None = None


class Exchange(ApiModel):
    id: int | None = None
    name: str | None = None
    workingSchedules: list[WorkingSchedule] | None = None


class Instrument(ApiModel):
    currency: str | None = None
    isin: str | None = None
    name: str | None = None
    ticker: str | None = None


class TradeableInstrument(ApiModel):
    addedOn: datetime | None = None
    currencyCode: str | None = None
    extendedHours: bool | None = None
    isin: str | None = None
    maxOpenQuantity: float | None = None
    minTradeQuantity: float | None = None
    name: str | None = None
    shortName: str | None = None
    ticker: str | None = None
    type: OpenEnum[TradeableInstrumentTypeEnum] | None = None
    workingScheduleId: int | None = None
