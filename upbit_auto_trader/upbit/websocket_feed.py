from __future__ import annotations

import random
import time


class WebSocketFeed:
    """WebSocket placeholder. Replace with real Upbit websocket stream."""

    def get_next_tick(self, timeout: float = 1.0) -> dict:
        time.sleep(min(timeout, 0.2))
        return {
            "symbol": "KRW-BTC",
            "price": 100000000 + random.uniform(-100000, 100000),
            "volume": random.uniform(1.0, 10.0),
            "btc_price": 100000000 + random.uniform(-100000, 100000),
            "kimp": random.uniform(-2.0, 8.0),
            "btc_dominance": random.uniform(45.0, 60.0),
        }
