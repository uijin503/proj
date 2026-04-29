from __future__ import annotations

import gc
import json
import logging
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    project_root: Path
    max_ui_log_rows: int
    max_chart_points: int
    mode: str
    min_ai_confidence: int
    strong_buy_confidence: int
    max_buy_amount_krw: float
    max_positions: int
    allow_new_buy_in_bear_market: bool


class TradingEngine:
    def __init__(self, config_path: str | None = None):
        self._stop_event = threading.Event()
        self._log_queue: queue.Queue[str] = queue.Queue(maxsize=1000)
        self._positions: dict[str, dict[str, float]] = {}
        self._ai_queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=500)

        default_config = Path(__file__).resolve().parents[1] / "config.yaml"
        self._config_path = Path(config_path) if config_path else default_config

        with self._config_path.open("r", encoding="utf-8") as fp:
            raw = yaml.safe_load(fp)

        root = self._config_path.parent
        self.config = EngineConfig(
            project_root=root,
            max_ui_log_rows=int(raw["system"]["max_ui_log_rows"]),
            max_chart_points=int(raw["system"]["max_chart_points"]),
            mode=str(raw["app"]["mode"]),
            min_ai_confidence=int(raw["ai"]["min_confidence"]),
            strong_buy_confidence=int(raw["ai"]["strong_buy_confidence"]),
            max_buy_amount_krw=float(raw["trading"]["max_buy_amount_krw"]),
            max_positions=int(raw["trading"]["max_positions"]),
            allow_new_buy_in_bear_market=bool(raw["trading"].get("allow_new_buy_in_bear_market", False)),
        )
        self.bucket = TokenBucket(capacity=8, refill_rate_per_sec=8)
        self.regime = MarketRegimeDetector()
        self.risk = RiskManager(
            max_buy_amount_krw=self.config.max_buy_amount_krw,
            max_positions=self.config.max_positions,
            daily_loss_limit_pct=float(raw["trading"]["daily_loss_limit_pct"]),
            max_consecutive_losses=int(raw["trading"]["max_consecutive_losses"]),
        )
        self.upbit = UpbitClient(token_bucket=self.bucket, mode=self.config.mode)
        self.feed = WebSocketFeed()
        self.ai = GeminiClient(model_name=raw["ai"]["model_name"])
        db_path = root / "database" / "trades.db"
        self.rag = RAGMemory(db_path=str(db_path))
        self.notifier = Notifier()
        self._stop_loss_pct = float(raw["risk"]["stop_loss_pct"])
        self._ai_worker = threading.Thread(target=self._ai_loop, daemon=True)

    def run_forever(self) -> None:
        LOGGER.info("TradingEngine started")
        self.log(f"Engine mode={self.config.mode}")
        self._ai_worker.start()

        while not self._stop_event.is_set():
            try:
                tick = self.feed.get_next_tick(timeout=1.0)
                if not tick:
                    continue

                regime = self.regime.update(float(tick.get("btc_price", 0.0)))
                if regime == "BEAR" and not self.config.allow_new_buy_in_bear_market:
                    self.log("BEAR market detected: new buys blocked")

                candidate = self._build_candidate(tick, regime)
                if self._score_candidate(candidate) >= 80:
                    self._ai_queue.put_nowait(candidate)

                self._trim_memory()
            except queue.Full:
                self.log("AI queue full, dropped candidate")
            except Exception as exc:
                LOGGER.exception("Engine loop error: %s", exc)
                self.log(f"Engine recovered from error: {exc}")
                time.sleep(1)

    def _score_candidate(self, candidate: dict[str, Any]) -> int:
        score = 0
        if candidate["volume"] > 2.0:
            score += 20
        if candidate["change_pct"] > 0.15:
            score += 20
        if candidate["regime"] == "BULL":
            score += 20
        if -1.0 <= candidate["kimp"] <= 6.0:
            score += 20
        if 45 <= candidate["btc_dominance"] <= 60:
            score += 20
        return score

    def _ai_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                candidate = self._ai_queue.get(timeout=1)
                can_open, reason = self.risk.can_open_position(
                    current_positions=len(self._positions),
                    order_amount_krw=self.config.max_buy_amount_krw,
                )
                if not can_open:
                    self.log(f"Risk blocked buy: {reason}")
                    continue

                if candidate["regime"] == "BEAR" and not self.config.allow_new_buy_in_bear_market:
                    continue

                ai_raw = self.ai.analyze_candidate(candidate, self.rag.search_similar(candidate))
                decision = self._safe_parse_ai(ai_raw)
                confidence = int(decision.get("confidence_score", 0))

                if decision.get("decision") == "BUY" and confidence >= self.config.min_ai_confidence:
                    self._open_position(candidate)
                    self.log(f"BUY {candidate['symbol']} / AI={confidence}")
                else:
                    self.log(f"HOLD {candidate['symbol']} / AI={confidence}")
            except queue.Empty:
                continue
            except Exception as exc:
                self.log(f"AI worker recovered from error: {exc}")

    def _safe_parse_ai(self, ai_raw: str) -> dict[str, Any]:
        try:
            return json.loads(ai_raw)
        except Exception:
            return {
                "decision": "HOLD",
                "confidence_score": 0,
                "reason": f"invalid ai response: {ai_raw[:80]}",
                "recommended_stop_loss": -2.5,
            }

    def _open_position(self, candidate: dict[str, Any]) -> None:
        symbol = candidate["symbol"]
        if symbol in self._positions:
            return
        price = float(candidate["price"])
        qty = self.config.max_buy_amount_krw / price if price > 0 else 0
        self._positions[symbol] = {"avg_price": price, "qty": qty}
        memory = {
            "symbol": symbol,
            "decision": "BUY",
            "pnl_pct": 0.0,
            "reason": "score+risk+ai passed",
            "created_at": time.time(),
        }
        self.rag.save_trade_memory(memory)


    def get_settings_snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.config.mode,
            "max_buy_amount_krw": self.config.max_buy_amount_krw,
            "max_positions": self.config.max_positions,
            "min_ai_confidence": self.config.min_ai_confidence,
            "allow_new_buy_in_bear_market": self.config.allow_new_buy_in_bear_market,
            "stop_loss_pct": getattr(self, "_stop_loss_pct", -2.5),
        }

    def update_settings(self, payload: dict[str, Any]) -> None:
        with self._config_path.open("r", encoding="utf-8") as fp:
            raw = yaml.safe_load(fp)

        raw["app"]["mode"] = payload["mode"]
        raw["trading"]["max_buy_amount_krw"] = float(payload["max_buy_amount_krw"])
        raw["trading"]["max_positions"] = int(payload["max_positions"])
        raw["trading"]["allow_new_buy_in_bear_market"] = bool(payload["allow_new_buy_in_bear_market"])
        raw["ai"]["min_confidence"] = int(payload["min_ai_confidence"])
        raw["risk"]["stop_loss_pct"] = float(payload["stop_loss_pct"])

        with self._config_path.open("w", encoding="utf-8") as fp:
            yaml.safe_dump(raw, fp, sort_keys=False, allow_unicode=True)

        self.config.mode = raw["app"]["mode"]
        self.config.max_buy_amount_krw = float(raw["trading"]["max_buy_amount_krw"])
        self.config.max_positions = int(raw["trading"]["max_positions"])
        self.config.min_ai_confidence = int(raw["ai"]["min_confidence"])
        self.config.allow_new_buy_in_bear_market = bool(raw["trading"]["allow_new_buy_in_bear_market"])
        self._stop_loss_pct = float(raw["risk"]["stop_loss_pct"])

        self.risk.max_buy_amount_krw = self.config.max_buy_amount_krw
        self.risk.max_positions = self.config.max_positions
        self.upbit.mode = self.config.mode
        self.log("Settings updated from UI")

    def stop(self) -> None:
        self._stop_event.set()

    def emergency_stop(self) -> None:
        self.risk.trigger_emergency_stop()
        self.log("EMERGENCY STOP: force liquidating all positions")
        self._positions.clear()
        self.upbit.sell_all_market()

    def get_status(self) -> dict[str, Any]:
        return {
            "mode": self.config.mode,
            "positions": len(self._positions),
            "emergency": self.risk.state.emergency_stop,
            "daily_pnl_pct": self.risk.state.daily_pnl_pct,
        }

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

    def _build_candidate(self, tick: dict[str, Any], regime: str) -> dict[str, Any]:
        return {
            "symbol": tick.get("symbol", "KRW-BTC"),
            "price": float(tick.get("price", 0.0)),
            "volume": float(tick.get("volume", 0.0)),
            "change_pct": float(tick.get("change_pct", 0.0)),
            "regime": regime,
            "kimp": float(tick.get("kimp", 0.0)),
            "btc_dominance": float(tick.get("btc_dominance", 0.0)),
        }

    def _trim_memory(self) -> None:
        if self._ai_queue.qsize() > self.config.max_ui_log_rows:
            while self._ai_queue.qsize() > self.config.max_ui_log_rows:
                self._ai_queue.get_nowait()
        gc.collect()
