from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from .base import ApiModel, RequestModel
from .metadata import Instrument
from .orders import Order


class HistoryTransactionTypeEnum(StrEnum):
    WITHDRAW = "WITHDRAW"
    DEPOSIT = "DEPOSIT"
    FEE = "FEE"
    TRANSFER = "TRANSFER"


class ReportResponseStatusEnum(StrEnum):
    Queued = "Queued"
    Processing = "Processing"
    Running = "Running"
    Canceled = "Canceled"
    Failed = "Failed"
    Finished = "Finished"


class EnqueuedReportResponse(ApiModel):
    reportId: int


class Tax(ApiModel):
    fillId: str | None = None
    name: str | None = None
    quantity: float | None = None
    timeCharged: datetime | None = None


class FillWalletImpact(ApiModel):
    currency: str | None = None
    fxRate: float | None = None
    netValue: float | None = None
    realisedProfitLoss: float | None = None
    taxes: list[Tax] | None = None


class Fill(ApiModel):
    filledAt: datetime | None = None
    id: int | None = None
    price: float | None = None
    quantity: float | None = None
    tradingMethod: str | None = None
    type: str | None = None
    walletImpact: FillWalletImpact | None = None


class HistoricalOrder(ApiModel):
    fill: Fill | None = None
    order: Order | None = None


class HistoryDividendItem(ApiModel):
    amount: float | None = None
    amountInEuro: float | None = None
    currency: str | None = None
    grossAmountPerShare: float | None = None
    instrument: Instrument | None = None
    paidOn: datetime | None = None
    quantity: float | None = None
    reference: str | None = None
    ticker: str | None = None
    tickerCurrency: str | None = None
    type: str | None = None


class HistoryTransactionItem(ApiModel):
    amount: float | None = None
    currency: str | None = None
    dateTime: datetime | None = None
    reference: str | None = None
    type: HistoryTransactionTypeEnum | None = None


class PaginatedResponseHistoricalOrder(ApiModel):
    items: list[HistoricalOrder]
    nextPagePath: str | None = None


class PaginatedResponseHistoryDividendItem(ApiModel):
    items: list[HistoryDividendItem]
    nextPagePath: str | None = None


class PaginatedResponseHistoryTransactionItem(ApiModel):
    items: list[HistoryTransactionItem]
    nextPagePath: str | None = None


class ReportDataIncluded(RequestModel):
    includeDividends: bool | None = True
    includeInterest: bool | None = True
    includeOrders: bool | None = True
    includeTransactions: bool | None = True


class PublicReportRequest(RequestModel):
    dataIncluded: ReportDataIncluded | None = None
    timeFrom: datetime | None = None
    timeTo: datetime | None = None

    @model_validator(mode="after")
    def ordered_dates(self) -> Self:
        for value in (self.timeFrom, self.timeTo):
            if value is not None and value.tzinfo is None:
                raise ValueError("Export dates must include a timezone")
        if self.timeFrom and self.timeTo and self.timeFrom > self.timeTo:
            raise ValueError("Export start must precede end")
        return self


class ReportResponse(ApiModel):
    dataIncluded: ReportDataIncluded | None = None
    downloadLink: str | None = None
    reportId: int | None = None
    status: ReportResponseStatusEnum | None = None
    timeFrom: datetime | None = None
    timeTo: datetime | None = None
