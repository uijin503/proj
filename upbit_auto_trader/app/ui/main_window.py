from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self, engine, engine_thread):
        super().__init__()
        self.engine = engine
        self.engine_thread = engine_thread
        self.setWindowTitle("Upbit AI Auto Trader")
        self.resize(1440, 900)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._flush_logs)
        self._timer.start(500)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        sidebar = QListWidget()
        sidebar.addItems(
            [
                "대시보드",
                "실시간 감시",
                "AI 분석",
                "보유 코인",
                "매매 달력",
                "백테스트",
                "학습 기록",
                "설정",
                "로그",
                "긴급 정지",
            ]
        )
        sidebar.setMaximumWidth(220)

        main_col = QVBoxLayout()
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("총 자산"))
        total = QLabel("₩ 0")
        total.setObjectName("Accent")
        card_layout.addWidget(total)
        card_layout.addWidget(QLabel("오늘 손익"))
        pnl = QLabel("+0.00%")
        pnl.setObjectName("Profit")
        card_layout.addWidget(pnl)

        emergency = QPushButton("🛑 긴급 정지")
        emergency.setObjectName("EmergencyStop")
        emergency.clicked.connect(self._confirm_emergency_stop)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)

        main_col.addWidget(card)
        main_col.addWidget(emergency)
        main_col.addWidget(self.logs)

        layout.addWidget(sidebar)
        layout.addLayout(main_col)

    def _flush_logs(self) -> None:
        logs = self.engine.drain_logs()
        if not logs:
            return
        for line in logs[-1000:]:
            self.logs.append(line)

    def _confirm_emergency_stop(self) -> None:
        reply = QMessageBox.question(
            self,
            "긴급 정지 확인",
            "모든 매매를 중단하고 보유 코인을 전량 시장가 매도할까요?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.engine.emergency_stop()

    def closeEvent(self, event) -> None:
        self.engine_thread.stop()
        return super().closeEvent(event)
