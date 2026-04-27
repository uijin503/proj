from __future__ import annotations

import pandas as pd


class BacktestEngine:
    def run(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"win_rate": 0.0, "return_pct": 0.0, "max_drawdown_pct": 0.0}
        returns = df["close"].pct_change().fillna(0)
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        return {
            "win_rate": round((returns > 0).mean() * 100, 2),
            "return_pct": round((cumulative.iloc[-1] - 1) * 100, 2),
            "max_drawdown_pct": round(drawdown.min() * 100, 2),
        }
