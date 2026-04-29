from __future__ import annotations

import logging

import pyupbit

LOGGER = logging.getLogger(__name__)


class UpbitClient:
    def __init__(self, token_bucket, mode: str = "paper"):
        self.token_bucket = token_bucket
        self.mode = mode

    def get_ticker(self, symbol: str) -> float:
        self.token_bucket.acquire()
        try:
            price = pyupbit.get_current_price(symbol)
            return float(price) if price else 0.0
        except Exception as exc:
            LOGGER.warning("Failed to fetch ticker %s: %s", symbol, exc)
            return 0.0

    def sell_all_market(self) -> None:
        if self.mode in {"paper", "test"}:
            LOGGER.warning("[%s mode] virtual sell-all executed.", self.mode)
            return
        LOGGER.warning("Real sell-all hook called. Implement signed order API call here.")
