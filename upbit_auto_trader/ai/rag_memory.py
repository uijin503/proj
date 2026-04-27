from __future__ import annotations

from database.sqlite_store import SQLiteStore


class RAGMemory:
    def __init__(self, db_path: str):
        self.store = SQLiteStore(db_path)
        self.store.init_schema()

    def save_trade_memory(self, payload: dict) -> None:
        self.store.insert_memory(payload)

    def search_similar(self, current: dict) -> list[dict]:
        return self.store.find_similar_by_symbol(current.get("symbol", ""), limit=10)
