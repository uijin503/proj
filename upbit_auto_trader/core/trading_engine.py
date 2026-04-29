import gc
import random
import time
from collections import deque
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from core.risk_manager import RiskManager


class TradingEngine(QThread):
    log_signal = Signal(str, str)
    status_signal = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._logs = deque(maxlen=1000)
        self.risk = RiskManager(max_daily_loss_pct=-3.0, max_positions=3, consecutive_stop_limit=3)

    def start_trading(self) -> None:
        self._running = True
        if not self.isRunning():
            self.start()

    def stop_trading(self) -> None:
        self._running = False

    def run(self) -> None:
        self.status_signal.emit("RUNNING")
        while self._running:
            allowed, reason = self.risk.can_enter()
            score = random.randint(50, 95)
            action = "BUY_CANDIDATE" if score >= 80 and allowed else "SKIP"
            message = f"{datetime.utcnow().isoformat()} | score={score} | action={action} | risk={reason}"
            self._logs.append(message)
            self.log_signal.emit("info" if action != "SKIP" else "warn", message)
            if len(self._logs) % 50 == 0:
                gc.collect()
            time.sleep(1)
        self.status_signal.emit("STOPPED")
