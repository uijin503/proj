from dataclasses import dataclass, field


@dataclass
class RiskState:
    daily_pnl_pct: float = 0.0
    consecutive_losses: int = 0
    emergency_stop: bool = False


@dataclass
class RiskManager:
    max_buy_amount_krw: float
    max_positions: int
    daily_loss_limit_pct: float
    max_consecutive_losses: int
    state: RiskState = field(default_factory=RiskState)

    def can_open_position(self, current_positions: int, order_amount_krw: float) -> tuple[bool, str]:
        if self.state.emergency_stop:
            return False, "Emergency stop active"
        if current_positions >= self.max_positions:
            return False, "Max positions reached"
        if order_amount_krw > self.max_buy_amount_krw:
            return False, "Order size exceeds max buy amount"
        if self.state.daily_pnl_pct <= self.daily_loss_limit_pct:
            return False, "Daily loss limit reached"
        if self.state.consecutive_losses >= self.max_consecutive_losses:
            return False, "Consecutive loss limit reached"
        return True, "OK"

    def register_trade_result(self, pnl_pct: float) -> None:
        self.state.daily_pnl_pct += pnl_pct
        if pnl_pct < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0

    def trigger_emergency_stop(self) -> None:
        self.state.emergency_stop = True
