import threading
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate_per_sec = refill_rate_per_sec
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_sec)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

            time.sleep(0.1)
