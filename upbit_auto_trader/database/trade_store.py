import sqlite3
from pathlib import Path


class TradeStore:
    def __init__(self, db_path: str = "trade_history.db") -> None:
        self.path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trades(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    pnl REAL,
                    ai_review TEXT
                )
                """
            )

    def log_trade(self, ts: str, symbol: str, side: str, pnl: float, ai_review: str) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO trades(ts, symbol, side, pnl, ai_review) VALUES (?, ?, ?, ?, ?)",
                (ts, symbol, side, pnl, ai_review),
            )
