from __future__ import annotations

import logging

import pyupbit

LOGGER = logging.getLogger(__name__)


class UpbitClient:
    def __init__(self, token_bucket):
        self.token_bucket = token_bucket
        self.client = None

    def get_ticker(self, symbol: str) -> dict:
        self.token_bucket.acquire()
        return pyupbit.get_current_price(symbol)

    def sell_all_market(self) -> None:
        LOGGER.warning("Market sell-all triggered (stub). Connect signed Upbit client here.")
