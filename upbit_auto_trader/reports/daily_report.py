from __future__ import annotations

from datetime import datetime
from pathlib import Path


class DailyReportWriter:
    def __init__(self, out_dir: str = "reports"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def write(self, summary: dict) -> Path:
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        path = self.out_dir / f"daily_report_{date_key}.md"
        body = (
            f"# Daily Auto Report ({date_key})\n\n"
            f"- Total PnL: {summary.get('total_pnl_pct', 0)}%\n"
            f"- Win Rate: {summary.get('win_rate', 0)}%\n"
            f"- Suggested Improvements: {summary.get('improvements', 'N/A')}\n"
        )
        path.write_text(body, encoding="utf-8")
        return path
