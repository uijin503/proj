import sys
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.trading_engine import TradingEngine


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Upbit AI Auto Trader")
        self.resize(1200, 760)
        self.engine = TradingEngine()
        self.engine.log_signal.connect(self.append_log)
        self.engine.status_signal.connect(self.set_status)

        self.status = QLabel("Status: IDLE")
        self.logs = QListWidget()

        start_btn = QPushButton("자동매매 시작")
        pause_btn = QPushButton("일시정지")
        stop_btn = QPushButton("중지")
        emergency_btn = QPushButton("긴급 정지")
        emergency_btn.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")

        start_btn.clicked.connect(self.engine.start_trading)
        pause_btn.clicked.connect(self.engine.stop_trading)
        stop_btn.clicked.connect(self.engine.stop_trading)
        emergency_btn.clicked.connect(self.emergency_stop)

        sidebar = QVBoxLayout()
        for name in ["대시보드", "매매 달력", "백테스트", "학습 기록", "설정", "로그"]:
            sidebar.addWidget(QPushButton(name))
        sidebar.addStretch(1)

        main = QVBoxLayout()
        main.addWidget(self.status)
        controls = QHBoxLayout()
        for w in [start_btn, pause_btn, stop_btn, emergency_btn]:
            controls.addWidget(w)
        main.addLayout(controls)
        main.addWidget(self.logs)

        root = QHBoxLayout()
        left = QWidget()
        left.setLayout(sidebar)
        center = QWidget()
        center.setLayout(main)
        root.addWidget(left, 1)
        root.addWidget(center, 4)

        wrapper = QWidget()
        wrapper.setLayout(root)
        self.setCentralWidget(wrapper)
        self.setStyleSheet("QMainWindow { background: #121212; color: #efefef; } QPushButton { padding: 8px; }")

    def append_log(self, level: str, message: str) -> None:
        self.logs.insertItem(0, f"[{level.upper()}] {message}")
        if self.logs.count() > 1000:
            self.logs.takeItem(self.logs.count() - 1)

    def set_status(self, status: str) -> None:
        self.status.setText(f"Status: {status}")

    def emergency_stop(self) -> None:
        self.engine.stop_trading()
        self.append_log("error", "EMERGENCY STOP triggered. Order lock enabled.")


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
