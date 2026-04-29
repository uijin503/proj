from __future__ import annotations

from collections import defaultdict


class TradeCalendarSummary:
    def __init__(self):
        self._daily = defaultdict(lambda: {"pnl": 0.0, "trades": 0, "wins": 0})

    def add_trade(self, date_key: str, pnl_pct: float) -> None:
        bucket = self._daily[date_key]
        bucket["pnl"] += pnl_pct
        bucket["trades"] += 1
        if pnl_pct > 0:
            bucket["wins"] += 1

    def get_day(self, date_key: str) -> dict:
        day = self._daily.get(date_key, {"pnl": 0.0, "trades": 0, "wins": 0})
        win_rate = (day["wins"] / day["trades"] * 100) if day["trades"] else 0.0
        return {**day, "win_rate": round(win_rate, 2)}
