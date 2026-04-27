from __future__ import annotations

import asyncio
import gc
import json
import logging
import queue
import threading
import time
from dataclasses import dataclass

import yaml

from ai.gemini_client import GeminiClient
from ai.rag_memory import RAGMemory
from core.api_scheduler import TokenBucket
from core.market_regime import MarketRegimeDetector
from core.risk_manager import RiskManager
from notifications.notifier import Notifier
from upbit.client import UpbitClient
from upbit.websocket_feed import WebSocketFeed

LOGGER = logging.getLogger(__name__)


@dataclass
class EngineConfig:
    max_ui_log_rows: int = 1000
    max_chart_points: int = 1000


class TradingEngine:
    def __init__(self, config_path: str = "config.yaml"):
        self._stop_event = threading.Event()
        self._log_queue: queue.Queue[str] = queue.Queue(maxsize=1000)

        with open(config_path, "r", encoding="utf-8") as fp:
            raw = yaml.safe_load(fp)

        self.config = EngineConfig(
            max_ui_log_rows=raw["system"]["max_ui_log_rows"],
            max_chart_points=raw["system"]["max_chart_points"],
        )
        self.bucket = TokenBucket(capacity=8, refill_rate_per_sec=8)
        self.regime = MarketRegimeDetector()
        self.risk = RiskManager(
            max_buy_amount_krw=raw["trading"]["max_buy_amount_krw"],
            max_positions=raw["trading"]["max_positions"],
            daily_loss_limit_pct=raw["trading"]["daily_loss_limit_pct"],
            max_consecutive_losses=raw["trading"]["max_consecutive_losses"],
        )
        self.upbit = UpbitClient(token_bucket=self.bucket)
        self.feed = WebSocketFeed()
        self.ai = GeminiClient(model_name=raw["ai"]["model_name"])
        self.rag = RAGMemory(db_path="database/trades.db")
        self.notifier = Notifier()
        self.ai_queue: queue.Queue[dict] = queue.Queue(maxsize=500)
        self._ai_worker = threading.Thread(target=self._ai_loop, daemon=True)

    def run_forever(self) -> None:
        LOGGER.info("TradingEngine started")
        self._ai_worker.start()
        while not self._stop_event.is_set():
            try:
                tick = self.feed.get_next_tick(timeout=1.0)
                if not tick:
                    continue

                regime = self.regime.update(tick.get("btc_price", 0.0))
                if regime == "BEAR":
                    self.log("BEAR market detected: new buys disabled")

                candidate = self._build_candidate(tick, regime)
                self.ai_queue.put_nowait(candidate)
                self._trim_memory()
            except queue.Full:
                self.log("AI queue full, skipping candidate")
            except Exception as exc:  # 안정성 우선
                LOGGER.exception("Engine loop error: %s", exc)
                self.log(f"Engine recovered from error: {exc}")
                time.sleep(1)

    def _ai_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                candidate = self.ai_queue.get(timeout=1)
                decision = self.ai.analyze_candidate(candidate, self.rag.search_similar(candidate))
                payload = json.loads(decision)
                self.log(f"AI decision={payload['decision']} score={payload['confidence_score']}")
            except queue.Empty:
                continue
            except Exception as exc:
                self.log(f"AI worker recovered from error: {exc}")

    def _build_candidate(self, tick: dict, regime: str) -> dict:
        return {
            "symbol": tick.get("symbol", "KRW-BTC"),
            "price": tick.get("price", 0.0),
            "volume": tick.get("volume", 0.0),
            "regime": regime,
            "kimp": tick.get("kimp", 0.0),
            "btc_dominance": tick.get("btc_dominance", 0.0),
        }

    def stop(self) -> None:
        self._stop_event.set()

    def emergency_stop(self) -> None:
        self.risk.trigger_emergency_stop()
        self.log("EMERGENCY STOP: selling all positions and locking new orders")
        self.upbit.sell_all_market()

    def log(self, message: str) -> None:
        try:
            self._log_queue.put_nowait(message)
        except queue.Full:
            _ = self._log_queue.get_nowait()
            self._log_queue.put_nowait(message)

    def drain_logs(self) -> list[str]:
        items: list[str] = []
        while not self._log_queue.empty():
            items.append(self._log_queue.get_nowait())
        return items

    def _trim_memory(self) -> None:
        if self.ai_queue.qsize() > self.config.max_ui_log_rows:
            while self.ai_queue.qsize() > self.config.max_ui_log_rows:
                self.ai_queue.get_nowait()
        gc.collect()
