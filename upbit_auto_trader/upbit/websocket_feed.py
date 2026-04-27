from __future__ import annotations

import random
import time


class WebSocketFeed:
    """Local simulation feed for stable desktop testing.

    Replace this class with a real Upbit websocket client for production.
    """

    def __init__(self):
        self._last_price = 100000000.0

    def get_next_tick(self, timeout: float = 1.0) -> dict:
        time.sleep(min(timeout, 0.2))
        delta = random.uniform(-120000, 120000)
        new_price = max(1000.0, self._last_price + delta)
        change_pct = ((new_price - self._last_price) / self._last_price) * 100
        self._last_price = new_price

        return {
            "symbol": "KRW-BTC",
            "price": new_price,
            "volume": random.uniform(1.0, 12.0),
            "change_pct": change_pct,
            "btc_price": new_price,
            "kimp": random.uniform(-2.0, 8.0),
            "btc_dominance": random.uniform(45.0, 60.0),
        }
