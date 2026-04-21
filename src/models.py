from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    # Trading 212's public API is still evolving. Ignoring unknown fields keeps
    # additive upstream changes from breaking the MCP server.
    model_config = ConfigDict(extra="ignore")


# --- ENUMS ---
class DividendCashActionEnum(str, Enum):
    REINVEST = "REINVEST"
    TO_ACCOUNT_CASH = "TO_ACCOUNT_CASH"


class Environment(str, Enum):
    DEMO = "demo"
    LIVE = "live"


class AccountBucketResultStatusEnum(str, Enum):
    AHEAD = "AHEAD"
    ON_TRACK = "ON_TRACK"
    BEHIND = "BEHIND"


class HistoryTransactionTypeEnum(str, Enum):
    WITHDRAW = "WITHDRAW"
    DEPOSIT = "DEPOSIT"
    FEE = "FEE"
    TRANSFER = "TRANSFER"


class LimitRequestTimeValidityEnum(str, Enum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class OrderStatusEnum(str, Enum):
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


class OrderStrategyEnum(str, Enum):
    QUANTITY = "QUANTITY"
    VALUE = "VALUE"


class OrderTypeEnum(str, Enum):
    LIMIT = "LIMIT"
    STOP = "STOP"
    MARKET = "MARKET"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSideEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PositionInitiatedFromEnum(str, Enum):
    API = "API"
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"
    SYSTEM = "SYSTEM"
    AUTOINVEST = "AUTOINVEST"


class ReportResponseStatusEnum(str, Enum):
    Queued = "Queued"
    Processing = "Processing"
    Running = "Running"
    Canceled = "Canceled"
    Failed = "Failed"
    Finished = "Finished"


class StopLimitRequestTimeValidityEnum(str, Enum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class StopRequestTimeValidityEnum(str, Enum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class TimeEventTypeEnum(str, Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    BREAK_START = "BREAK_START"
    BREAK_END = "BREAK_END"
    PRE_MARKET_OPEN = "PRE_MARKET_OPEN"
    AFTER_HOURS_OPEN = "AFTER_HOURS_OPEN"
    AFTER_HOURS_CLOSE = "AFTER_HOURS_CLOSE"
    OVERNIGHT_OPEN = "OVERNIGHT_OPEN"


class TradeableInstrumentTypeEnum(str, Enum):
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


class TimeValidityEnum(str, Enum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


# --- MODELS ---
class Cash(ApiModel):
    availableToTrade: Optional[float] = None
    inPies: Optional[float] = None
    reservedForOrders: Optional[float] = None


class Investments(ApiModel):
    currentValue: Optional[float] = None
    realizedProfitLoss: Optional[float] = None
    totalCost: Optional[float] = None
    unrealizedProfitLoss: Optional[float] = None


class AccountSummary(ApiModel):
    cash: Optional[Cash] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    id: Optional[int] = None
    investments: Optional[Investments] = None
    totalValue: Optional[float] = None


class AccountBucketDetailedResponse(ApiModel):
    creationDate: Optional[datetime] = None
    dividendCashAction: Optional[DividendCashActionEnum] = None
    endDate: Optional[datetime] = None
    goal: Optional[float] = None
    icon: Optional[str] = None
    id: Optional[int] = None
    initialInvestment: Optional[float] = None
    instrumentShares: Optional[Dict[str, float]] = None
    name: Optional[str] = None
    publicUrl: Optional[str] = None


class InstrumentIssue(ApiModel):
    name: Optional[str] = None
    severity: Optional[str] = None


class InvestmentResult(ApiModel):
    priceAvgInvestedValue: Optional[float] = None
    priceAvgResult: Optional[float] = None
    priceAvgResultCoef: Optional[float] = None
    priceAvgValue: Optional[float] = None


class AccountBucketInstrumentResult(ApiModel):
    currentShare: Optional[float] = None
    expectedShare: Optional[float] = None
    issues: Optional[List[InstrumentIssue]] = None
    ownedQuantity: Optional[float] = None
    result: Optional[InvestmentResult] = None
    ticker: Optional[str] = None


class AccountBucketInstrumentsDetailedResponse(ApiModel):
    instruments: Optional[List[AccountBucketInstrumentResult]] = None
    settings: Optional[AccountBucketDetailedResponse] = None


class DividendDetails(ApiModel):
    gained: Optional[float] = None
    inCash: Optional[float] = None
    reinvested: Optional[float] = None


class AccountBucketResultResponse(ApiModel):
    cash: Optional[float] = None
    dividendDetails: Optional[DividendDetails] = None
    id: Optional[int] = None
    progress: Optional[float] = None
    result: Optional[InvestmentResult] = None
    status: Optional[AccountBucketResultStatusEnum] = None


class DuplicateBucketRequest(ApiModel):
    icon: Optional[str] = None
    name: Optional[str] = None


class EnqueuedReportResponse(ApiModel):
    reportId: int


class TimeEvent(ApiModel):
    date: datetime
    type: TimeEventTypeEnum


class WorkingSchedule(ApiModel):
    id: int
    timeEvents: List[TimeEvent]


class Exchange(ApiModel):
    id: int
    name: str
    workingSchedules: List[WorkingSchedule]


class Instrument(ApiModel):
    currency: Optional[str] = None
    isin: Optional[str] = None
    name: Optional[str] = None
    ticker: Optional[str] = None


class Tax(ApiModel):
    fillId: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[float] = None
    timeCharged: Optional[datetime] = None


class FillWalletImpact(ApiModel):
    currency: Optional[str] = None
    fxRate: Optional[float] = None
    netValue: Optional[float] = None
    realisedProfitLoss: Optional[float] = None
    taxes: Optional[List[Tax]] = None


class Fill(ApiModel):
    filledAt: Optional[datetime] = None
    id: Optional[int] = None
    price: Optional[float] = None
    quantity: Optional[float] = None
    tradingMethod: Optional[str] = None
    type: Optional[str] = None
    walletImpact: Optional[FillWalletImpact] = None


class LimitRequest(ApiModel):
    limitPrice: float
    quantity: float
    ticker: str
    timeValidity: LimitRequestTimeValidityEnum


class MarketRequest(ApiModel):
    extendedHours: bool = False
    quantity: float
    ticker: str


class Order(ApiModel):
    createdAt: Optional[datetime] = None
    currency: Optional[str] = None
    extendedHours: Optional[bool] = None
    filledQuantity: Optional[float] = None
    filledValue: Optional[float] = None
    id: Optional[int] = None
    initiatedFrom: Optional[PositionInitiatedFromEnum] = None
    instrument: Optional[Instrument] = None
    limitPrice: Optional[float] = None
    quantity: Optional[float] = None
    side: Optional[OrderSideEnum] = None
    status: Optional[OrderStatusEnum] = None
    stopPrice: Optional[float] = None
    strategy: Optional[OrderStrategyEnum] = None
    ticker: Optional[str] = None
    timeInForce: Optional[TimeValidityEnum] = None
    type: Optional[OrderTypeEnum] = None
    value: Optional[float] = None


class HistoricalOrder(ApiModel):
    fill: Optional[Fill] = None
    order: Optional[Order] = None


class HistoryDividendItem(ApiModel):
    amount: Optional[float] = None
    amountInEuro: Optional[float] = None
    currency: Optional[str] = None
    grossAmountPerShare: Optional[float] = None
    instrument: Optional[Instrument] = None
    paidOn: Optional[datetime] = None
    quantity: Optional[float] = None
    reference: Optional[str] = None
    ticker: Optional[str] = None
    tickerCurrency: Optional[str] = None
    type: Optional[str] = None


class HistoryTransactionItem(ApiModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    dateTime: Optional[datetime] = None
    reference: Optional[str] = None
    type: Optional[HistoryTransactionTypeEnum] = None


class PaginatedResponseHistoricalOrder(ApiModel):
    items: List[HistoricalOrder]
    nextPagePath: Optional[str] = None


class PaginatedResponseHistoryDividendItem(ApiModel):
    items: List[HistoryDividendItem]
    nextPagePath: Optional[str] = None


class PaginatedResponseHistoryTransactionItem(ApiModel):
    items: List[HistoryTransactionItem]
    nextPagePath: Optional[str] = None


class PieRequest(ApiModel):
    dividendCashAction: Optional[DividendCashActionEnum] = Field(
        default=None,
        description="How dividends are handled",
        examples=[
            DividendCashActionEnum.REINVEST,
            DividendCashActionEnum.TO_ACCOUNT_CASH,
        ],
    )
    endDate: Optional[datetime] = Field(default=None, format="date-time")
    goal: Optional[float] = Field(
        default=None,
        description="Total desired value of the pie in account currency",
    )
    icon: Optional[str] = None
    instrumentShares: Optional[Dict[str, float]] = Field(
        default=None,
        examples=[{"AAPL_US_EQ": 0.5, "MSFT_US_EQ": 0.5}],
        description="The shares of each instrument in the pie",
    )
    name: Optional[str] = None


class PlaceOrderError(ApiModel):
    clarification: Optional[str] = None
    code: Optional[str] = None


class PositionWalletImpact(ApiModel):
    currency: Optional[str] = None
    currentValue: Optional[float] = None
    fxImpact: Optional[float] = None
    totalCost: Optional[float] = None
    unrealizedProfitLoss: Optional[float] = None


class Position(ApiModel):
    averagePricePaid: Optional[float] = None
    createdAt: Optional[datetime] = None
    currentPrice: Optional[float] = None
    instrument: Optional[Instrument] = None
    quantity: Optional[float] = None
    quantityAvailableForTrading: Optional[float] = None
    quantityInPies: Optional[float] = None
    walletImpact: Optional[PositionWalletImpact] = None


class PositionRequest(ApiModel):
    ticker: str


class ReportDataIncluded(ApiModel):
    includeDividends: Optional[bool] = True
    includeInterest: Optional[bool] = True
    includeOrders: Optional[bool] = True
    includeTransactions: Optional[bool] = True


class PublicReportRequest(ApiModel):
    dataIncluded: Optional[ReportDataIncluded] = None
    timeFrom: Optional[datetime] = None
    timeTo: Optional[datetime] = None


class ReportResponse(ApiModel):
    dataIncluded: Optional[ReportDataIncluded] = None
    downloadLink: Optional[str] = None
    reportId: Optional[int] = None
    status: Optional[ReportResponseStatusEnum] = None
    timeFrom: Optional[datetime] = None
    timeTo: Optional[datetime] = None


class StopLimitRequest(ApiModel):
    limitPrice: float
    quantity: float
    stopPrice: float
    ticker: str
    timeValidity: StopLimitRequestTimeValidityEnum


class StopRequest(ApiModel):
    quantity: float
    stopPrice: float
    ticker: str
    timeValidity: StopRequestTimeValidityEnum


class TradeableInstrument(ApiModel):
    addedOn: Optional[datetime] = None
    currencyCode: Optional[str] = None
    extendedHours: Optional[bool] = None
    isin: Optional[str] = None
    maxOpenQuantity: Optional[float] = None
    minTradeQuantity: Optional[float] = None
    name: Optional[str] = None
    shortName: Optional[str] = None
    ticker: Optional[str] = None
    type: Optional[TradeableInstrumentTypeEnum] = None
    workingScheduleId: Optional[int] = None


WorkingSchedule.model_rebuild()
