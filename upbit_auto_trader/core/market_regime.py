from collections import deque


class MarketRegimeDetector:
    def __init__(self, lookback: int = 60):
        self.prices = deque(maxlen=lookback)

    def update(self, btc_price: float) -> str:
        self.prices.append(btc_price)
        if len(self.prices) < 10:
            return "SIDEWAYS"

        change_pct = (self.prices[-1] - self.prices[0]) / self.prices[0] * 100
        if change_pct > 1.0:
            return "BULL"
        if change_pct < -1.0:
            return "BEAR"
        return "SIDEWAYS"
