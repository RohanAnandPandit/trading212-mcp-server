from datetime import datetime
from enum import StrEnum

from pydantic import Field

from .base import ApiModel, RequestModel


class DividendCashActionEnum(StrEnum):
    REINVEST = "REINVEST"
    TO_ACCOUNT_CASH = "TO_ACCOUNT_CASH"


class AccountBucketResultStatusEnum(StrEnum):
    AHEAD = "AHEAD"
    ON_TRACK = "ON_TRACK"
    BEHIND = "BEHIND"


class AccountBucketDetailedResponse(ApiModel):
    creationDate: datetime | None = None
    dividendCashAction: DividendCashActionEnum | None = None
    endDate: datetime | None = None
    goal: float | None = None
    icon: str | None = None
    id: int | None = None
    initialInvestment: float | None = None
    instrumentShares: dict[str, float] | None = None
    name: str | None = None
    publicUrl: str | None = None


class InstrumentIssue(ApiModel):
    name: str | None = None
    severity: str | None = None


class InvestmentResult(ApiModel):
    priceAvgInvestedValue: float | None = None
    priceAvgResult: float | None = None
    priceAvgResultCoef: float | None = None
    priceAvgValue: float | None = None


class AccountBucketInstrumentResult(ApiModel):
    currentShare: float | None = None
    expectedShare: float | None = None
    issues: list[InstrumentIssue] | None = None
    ownedQuantity: float | None = None
    result: InvestmentResult | None = None
    ticker: str | None = None


class AccountBucketInstrumentsDetailedResponse(ApiModel):
    instruments: list[AccountBucketInstrumentResult] | None = None
    settings: AccountBucketDetailedResponse | None = None


class DividendDetails(ApiModel):
    gained: float | None = None
    inCash: float | None = None
    reinvested: float | None = None


class AccountBucketResultResponse(ApiModel):
    cash: float | None = None
    dividendDetails: DividendDetails | None = None
    id: int | None = None
    progress: float | None = None
    result: InvestmentResult | None = None
    status: AccountBucketResultStatusEnum | None = None


class DuplicateBucketRequest(RequestModel):
    icon: str | None = None
    name: str | None = None


class PieRequest(RequestModel):
    dividendCashAction: DividendCashActionEnum | None = Field(
        default=None,
        description="How dividends are handled",
        examples=[
            DividendCashActionEnum.REINVEST,
            DividendCashActionEnum.TO_ACCOUNT_CASH,
        ],
    )
    endDate: datetime | None = Field(default=None)
    goal: float | None = Field(
        default=None,
        description="Total desired value of the pie in account currency",
    )
    icon: str | None = None
    instrumentShares: dict[str, float] | None = Field(
        default=None,
        examples=[{"AAPL_US_EQ": 0.5, "MSFT_US_EQ": 0.5}],
        description="The shares of each instrument in the pie",
    )
    name: str | None = None
