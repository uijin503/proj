from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    decision TEXT,
                    pnl_pct REAL,
                    payload_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def insert_memory(self, payload: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO trade_memory(symbol, decision, pnl_pct, payload_json) VALUES (?, ?, ?, ?)",
                (
                    payload.get("symbol"),
                    payload.get("decision"),
                    payload.get("pnl_pct"),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    def find_similar_by_symbol(self, symbol: str, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_json
                FROM trade_memory
                WHERE symbol = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (symbol, limit),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
