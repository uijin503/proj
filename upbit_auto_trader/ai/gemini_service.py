import asyncio
from core.models import TradeDecision


class GeminiQueueService:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict] = asyncio.Queue()

    async def submit(self, payload: dict) -> None:
        await self._queue.put(payload)

    async def process_once(self) -> TradeDecision:
        payload = await self._queue.get()
        score = int(payload.get("score", 0))
        decision = "BUY" if score >= 80 else "HOLD"
        return TradeDecision(
            decision=decision,
            confidence_score=min(99, max(1, score)),
            reason="Queue-based AI gate evaluation",
            recommended_stop_loss=-2.5,
        )
