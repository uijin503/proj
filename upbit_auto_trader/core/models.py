from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MarketSnapshot:
    symbol: str
    price: float
    volume_ratio: float
    trend_score: float
    volatility_score: float
    orderbook_stability: float
    timestamp: datetime


@dataclass(slots=True)
class TradeDecision:
    decision: str
    confidence_score: int
    reason: str
    recommended_stop_loss: float
