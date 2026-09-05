from datetime import datetime

from pydantic import Field

from .base import ApiModel
from .metadata import Instrument


class Cash(ApiModel):
    availableToTrade: float | None = None
    inPies: float | None = None
    reservedForOrders: float | None = None


class Investments(ApiModel):
    currentValue: float | None = None
    realizedProfitLoss: float | None = None
    totalCost: float | None = None
    unrealizedProfitLoss: float | None = None


class AccountSummary(ApiModel):
    cash: Cash | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    id: int | None = None
    investments: Investments | None = None
    totalValue: float | None = None


class PositionWalletImpact(ApiModel):
    currency: str | None = None
    currentValue: float | None = None
    fxImpact: float | None = None
    totalCost: float | None = None
    unrealizedProfitLoss: float | None = None


class Position(ApiModel):
    averagePricePaid: float | None = None
    createdAt: datetime | None = None
    currentPrice: float | None = None
    instrument: Instrument | None = None
    quantity: float | None = None
    quantityAvailableForTrading: float | None = None
    quantityInPies: float | None = None
    walletImpact: PositionWalletImpact | None = None


class PositionRequest(ApiModel):
    ticker: str
