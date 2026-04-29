class RiskManager:
    def __init__(self, max_daily_loss_pct: float, max_positions: int, consecutive_stop_limit: int) -> None:
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_positions = max_positions
        self.consecutive_stop_limit = consecutive_stop_limit
        self.daily_pnl_pct = 0.0
        self.open_positions = 0
        self.consecutive_stop_count = 0

    def can_enter(self) -> tuple[bool, str]:
        if self.daily_pnl_pct <= self.max_daily_loss_pct:
            return False, "Daily loss limit reached"
        if self.open_positions >= self.max_positions:
            return False, "Max positions reached"
        if self.consecutive_stop_count >= self.consecutive_stop_limit:
            return False, "Consecutive stop loss limit reached"
        return True, "OK"
