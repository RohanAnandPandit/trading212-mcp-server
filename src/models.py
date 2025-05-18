from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# --- ENUMS ---
class DividendCashActionEnum(str, Enum):
    REINVEST = "REINVEST"
    TO_ACCOUNT_CASH = "TO_ACCOUNT_CASH"


class Environment(str, Enum):
    DEMO = "demo"
    LIVE = "live"


class InstrumentIssueNameEnum(str, Enum):
    DELISTED = "DELISTED"
    SUSPENDED = "SUSPENDED"
    NO_LONGER_TRADABLE = "NO_LONGER_TRADABLE"
    MAX_POSITION_SIZE_REACHED = "MAX_POSITION_SIZE_REACHED"
    APPROACHING_MAX_POSITION_SIZE = "APPROACHING_MAX_POSITION_SIZE"
    COMPLEX_INSTRUMENT_APP_TEST_REQUIRED = "COMPLEX_INSTRUMENT_APP_TEST_REQUIRED"


class InstrumentIssueSeverityEnum(str, Enum):
    IRREVERSIBLE = "IRREVERSIBLE"
    REVERSIBLE = "REVERSIBLE"
    INFORMATIVE = "INFORMATIVE"


class AccountBucketResultStatusEnum(str, Enum):
    AHEAD = "AHEAD"
    ON_TRACK = "ON_TRACK"
    BEHIND = "BEHIND"


class HistoricalOrderExecutorEnum(str, Enum):
    API = "API"
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"
    SYSTEM = "SYSTEM"
    AUTOINVEST = "AUTOINVEST"


class HistoricalOrderFillTypeEnum(str, Enum):
    TOTV = "TOTV"
    OTC = "OTC"


class HistoricalOrderStatusEnum(str, Enum):
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


class HistoricalOrderTimeValidityEnum(str, Enum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"


class HistoricalOrderTypeEnum(str, Enum):
    LIMIT = "LIMIT"
    STOP = "STOP"
    MARKET = "MARKET"
    STOP_LIMIT = "STOP_LIMIT"


class TaxNameEnum(str, Enum):
    COMMISSION_TURNOVER = "COMMISSION_TURNOVER"
    CURRENCY_CONVERSION_FEE = "CURRENCY_CONVERSION_FEE"
    FINRA_FEE = "FINRA_FEE"
    FRENCH_TRANSACTION_TAX = "FRENCH_TRANSACTION_TAX"
    PTM_LEVY = "PTM_LEVY"
    STAMP_DUTY = "STAMP_DUTY"
    STAMP_DUTY_RESERVE_TAX = "STAMP_DUTY_RESERVE_TAX"
    TRANSACTION_FEE = "TRANSACTION_FEE"


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


class PlaceOrderErrorCodeEnum(str, Enum):
    SellingEquityNotOwned = "SellingEquityNotOwned"
    CantLegalyTradeException = "CantLegalyTradeException"
    InsufficientResources = "InsufficientResources"
    InsufficientValueForStocksSell = "InsufficientValueForStocksSell"
    TargetPriceTooFar = "TargetPriceTooFar"
    TargetPriceTooClose = "TargetPriceTooClose"
    NotEligibleForISA = "NotEligibleForISA"
    ShareLendingAgreementNotAccepted = "ShareLendingAgreementNotAccepted"
    InstrumentNotFound = "InstrumentNotFound"
    MaxEquityBuyQuantityExceeded = "MaxEquityBuyQuantityExceeded"
    MaxEquitySellQuantityExceeded = "MaxEquitySellQuantityExceeded"
    LimitPriceMissing = "LimitPriceMissing"
    StopPriceMissing = "StopPriceMissing"
    TickerMissing = "TickerMissing"
    QuantityMissing = "QuantityMissing"
    MaxQuantityExceeded = "MaxQuantityExceeded"
    InvalidValue = "InvalidValue"
    InsufficientFreeForStocksException = "InsufficientFreeForStocksException"
    MinValueExceeded = "MinValueExceeded"
    MinQuantityExceeded = "MinQuantityExceeded"
    PriceTooFar = "PriceTooFar"
    UNDEFINED = "UNDEFINED"
    NotAvailableForRealMoneyAccounts = "NotAvailableForRealMoneyAccounts"


class PositionFrontendEnum(str, Enum):
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


# --- MODELS ---
class Account(BaseModel):
    currencyCode: str = Field(..., min_length=3, max_length=3,
                              description="ISO 4217", example="USD")
    id: int


class AccountBucketDetailedResponse(BaseModel):
    creationDate: Optional[datetime]
    dividendCashAction: Optional[DividendCashActionEnum]
    endDate: Optional[datetime]
    goal: Optional[float]
    icon: Optional[str]
    id: Optional[int]
    initialInvestment: Optional[float]
    instrumentShares: Optional[Dict[str, float]]
    name: Optional[str]
    publicUrl: Optional[str]


class InstrumentIssue(BaseModel):
    name: InstrumentIssueNameEnum
    severity: InstrumentIssueSeverityEnum


class InvestmentResult(BaseModel):
    priceAvgInvestedValue: Optional[float]
    priceAvgResult: Optional[float]
    priceAvgResultCoef: Optional[float]
    priceAvgValue: Optional[float]


class AccountBucketInstrumentResult(BaseModel):
    currentShare: Optional[float]
    expectedShare: Optional[float]
    issues: Optional[List[InstrumentIssue]]
    ownedQuantity: Optional[float]
    result: Optional[InvestmentResult]
    ticker: Optional[str]


class AccountBucketInstrumentsDetailedResponse(BaseModel):
    instruments: Optional[List[AccountBucketInstrumentResult]]
    settings: Optional[AccountBucketDetailedResponse]


class DividendDetails(BaseModel):
    gained: Optional[float]
    inCash: Optional[float]
    reinvested: Optional[float]


class AccountBucketResultResponse(BaseModel):
    cash: Optional[float]
    dividendDetails: Optional[DividendDetails]
    id: Optional[int]
    progress: Optional[float]
    result: Optional[InvestmentResult]
    status: Optional[AccountBucketResultStatusEnum]


class Cash(BaseModel):
    blocked: Optional[float]
    free: Optional[float]
    invested: Optional[float]
    pieCash: Optional[float]
    ppl: Optional[float]
    result: Optional[float]
    total: Optional[float]


class DuplicateBucketRequest(BaseModel):
    icon: Optional[str]
    name: Optional[str]


class EnqueuedReportResponse(BaseModel):
    reportId: int


class TimeEvent(BaseModel):
    date: datetime
    type: TimeEventTypeEnum


class WorkingSchedule(BaseModel):
    id: int
    timeEvents: List[TimeEvent]


class Exchange(BaseModel):
    id: int
    name: str
    workingSchedules: List[WorkingSchedule]


class Tax(BaseModel):
    fillId: Optional[str]
    name: Optional[TaxNameEnum]
    quantity: Optional[float]
    timeCharged: Optional[datetime]


class HistoricalOrder(BaseModel):
    dateCreated: Optional[datetime]
    dateExecuted: Optional[datetime]
    dateModified: Optional[datetime]
    executor: Optional[HistoricalOrderExecutorEnum]
    fillCost: Optional[float]
    fillId: Optional[int]
    fillPrice: Optional[float]
    fillResult: Optional[float]
    fillType: Optional[HistoricalOrderFillTypeEnum]
    filledQuantity: Optional[float]
    filledValue: Optional[float]
    id: Optional[int]
    limitPrice: Optional[float]
    orderedQuantity: Optional[float]
    orderedValue: Optional[float]
    parentOrder: Optional[int]
    status: Optional[HistoricalOrderStatusEnum]
    stopPrice: Optional[float]
    taxes: Optional[List[Tax]]
    ticker: Optional[str]
    timeValidity: Optional[HistoricalOrderTimeValidityEnum]
    type: Optional[HistoricalOrderTypeEnum]


class HistoryDividendItem(BaseModel):
    amount: Optional[float]
    amountInEuro: Optional[float]
    grossAmountPerShare: Optional[float]
    paidOn: Optional[datetime]
    quantity: Optional[float]
    reference: Optional[str]
    ticker: Optional[str]
    type: Optional[str]


class HistoryTransactionItem(BaseModel):
    amount: Optional[float]
    dateTime: Optional[datetime]
    reference: Optional[str]
    type: Optional[HistoryTransactionTypeEnum]


class LimitRequest(BaseModel):
    limitPrice: float
    quantity: float
    ticker: str
    timeValidity: LimitRequestTimeValidityEnum


class MarketRequest(BaseModel):
    quantity: float
    ticker: str


class Order(BaseModel):
    creationTime: Optional[datetime]
    filledQuantity: Optional[float]
    filledValue: Optional[float]
    id: Optional[int]
    limitPrice: Optional[float]
    quantity: Optional[float]
    status: Optional[OrderStatusEnum]
    stopPrice: Optional[float]
    strategy: Optional[OrderStrategyEnum]
    ticker: Optional[str]
    type: Optional[OrderTypeEnum]
    value: Optional[float]


class PaginatedResponseHistoricalOrder(BaseModel):
    items: List[HistoricalOrder]
    nextPagePath: Optional[str]


class PaginatedResponseHistoryDividendItem(BaseModel):
    items: List[HistoryDividendItem]
    nextPagePath: Optional[str]


class PaginatedResponseHistoryTransactionItem(BaseModel):
    items: List[HistoryTransactionItem]
    nextPagePath: Optional[str]


class PieRequest(BaseModel):
    dividendCashAction: Optional[DividendCashActionEnum]
    endDate: Optional[datetime]
    goal: Optional[float]
    icon: Optional[str]
    instrumentShares: Optional[Dict[str, float]]
    name: Optional[str]


class PlaceOrderError(BaseModel):
    clarification: Optional[str]
    code: Optional[PlaceOrderErrorCodeEnum]


class Position(BaseModel):
    averagePrice: Optional[float]
    currentPrice: Optional[float]
    frontend: Optional[PositionFrontendEnum]
    fxPpl: Optional[float]
    initialFillDate: Optional[datetime]
    maxBuy: Optional[float]
    maxSell: Optional[float]
    pieQuantity: Optional[float]
    ppl: Optional[float]
    quantity: Optional[float]
    ticker: Optional[str]


class PositionRequest(BaseModel):
    ticker: str


class ReportDataIncluded(BaseModel):
    includeDividends: Optional[bool]
    includeInterest: Optional[bool]
    includeOrders: Optional[bool]
    includeTransactions: Optional[bool]


class PublicReportRequest(BaseModel):
    dataIncluded: Optional[ReportDataIncluded]
    timeFrom: Optional[datetime]
    timeTo: Optional[datetime]


class ReportResponse(BaseModel):
    dataIncluded: Optional[ReportDataIncluded]
    downloadLink: Optional[str]
    reportId: Optional[int]
    status: Optional[ReportResponseStatusEnum]
    timeFrom: Optional[datetime]
    timeTo: Optional[datetime]


class StopLimitRequest(BaseModel):
    limitPrice: float
    quantity: float
    stopPrice: float
    ticker: str
    timeValidity: StopLimitRequestTimeValidityEnum


class StopRequest(BaseModel):
    quantity: float
    stopPrice: float
    ticker: str
    timeValidity: StopRequestTimeValidityEnum


class TradeableInstrument(BaseModel):
    addedOn: Optional[datetime]
    currencyCode: Optional[str]
    isin: Optional[str]
    maxOpenQuantity: Optional[float]
    minTradeQuantity: Optional[float]
    name: Optional[str]
    shortName: Optional[str]
    ticker: Optional[str]
    type: Optional[TradeableInstrumentTypeEnum]
    workingScheduleId: Optional[int]


# Fix forward references if needed
WorkingSchedule.model_rebuild()
