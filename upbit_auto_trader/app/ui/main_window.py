from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    MENU_ITEMS = [
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

    def __init__(self, engine, engine_thread):
        super().__init__()
        self.engine = engine
        self.engine_thread = engine_thread
        self.setWindowTitle("Upbit AI Auto Trader")
        self.resize(1440, 900)
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(500)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        self.sidebar = QListWidget()
        self.sidebar.addItems(self.MENU_ITEMS)
        self.sidebar.setMaximumWidth(220)
        self.sidebar.currentRowChanged.connect(self._on_menu_changed)

        self.pages = QStackedWidget()
        self._build_pages()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)
        self.sidebar.setCurrentRow(0)

    def _build_pages(self) -> None:
        self.pages.addWidget(self._make_dashboard_page())
        self.pages.addWidget(self._make_simple_page("실시간 감시", "실시간 모니터링 페이지"))
        self.pages.addWidget(self._make_simple_page("AI 분석", "AI 분석 결과 페이지"))
        self.pages.addWidget(self._make_simple_page("보유 코인", "현재 포지션 목록 페이지"))
        self.pages.addWidget(self._make_simple_page("매매 달력", "날짜별 수익/복기 페이지"))
        self.pages.addWidget(self._make_simple_page("백테스트", "전략 백테스트 페이지"))
        self.pages.addWidget(self._make_simple_page("학습 기록", "RAG 학습 기록 페이지"))
        self.pages.addWidget(self._make_settings_page())
        self.pages.addWidget(self._make_log_page())
        self.pages.addWidget(self._make_emergency_page())

    def _make_dashboard_page(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("자동매매 상태"))

        self.mode_label = QLabel("MODE: -")
        self.mode_label.setObjectName("Accent")
        card_layout.addWidget(self.mode_label)

        self.position_label = QLabel("보유 포지션: 0")
        card_layout.addWidget(self.position_label)

        self.pnl_label = QLabel("오늘 손익: 0.00%")
        self.pnl_label.setObjectName("Profit")
        card_layout.addWidget(self.pnl_label)

        self.dashboard_log_preview = QTextEdit()
        self.dashboard_log_preview.setReadOnly(True)
        self.dashboard_log_preview.setMaximumHeight(200)

        col.addWidget(card)
        col.addWidget(QLabel("실시간 로그 미리보기"))
        col.addWidget(self.dashboard_log_preview)
        return page

    def _make_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        card = QFrame()
        card.setObjectName("Card")
        form = QFormLayout(card)

        snapshot = self.engine.get_settings_snapshot()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["paper", "test", "live"])
        self.mode_combo.setCurrentText(snapshot["mode"])

        self.max_buy_spin = QSpinBox()
        self.max_buy_spin.setRange(5000, 50000000)
        self.max_buy_spin.setSingleStep(10000)
        self.max_buy_spin.setValue(int(snapshot["max_buy_amount_krw"]))

        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 20)
        self.max_positions_spin.setValue(int(snapshot["max_positions"]))

        self.min_ai_spin = QSpinBox()
        self.min_ai_spin.setRange(0, 100)
        self.min_ai_spin.setValue(int(snapshot["min_ai_confidence"]))

        self.bear_buy_check = QCheckBox("하락장에서 신규 매수 허용")
        self.bear_buy_check.setChecked(bool(snapshot["allow_new_buy_in_bear_market"]))

        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(-20.0, -0.1)
        self.stop_loss_spin.setSingleStep(0.1)
        self.stop_loss_spin.setValue(float(snapshot["stop_loss_pct"]))

        form.addRow("운영 모드", self.mode_combo)
        form.addRow("1회 매수 한도(KRW)", self.max_buy_spin)
        form.addRow("최대 보유 코인 수", self.max_positions_spin)
        form.addRow("AI 최소 신뢰도", self.min_ai_spin)
        form.addRow("손절(%)", self.stop_loss_spin)
        form.addRow("시장 조건", self.bear_buy_check)

        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self._save_settings)

        layout.addWidget(card)
        layout.addWidget(save_btn, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return page

    def _make_log_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        layout.addWidget(self.logs)
        return page

    def _make_emergency_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("긴급 정지 메뉴: 버튼을 누르면 신규 주문 잠금 + 전량 매도 시도")
        btn = QPushButton("🛑 긴급 정지 실행")
        btn.setObjectName("EmergencyStop")
        btn.clicked.connect(self._confirm_emergency_stop)
        layout.addWidget(label)
        layout.addWidget(btn)
        layout.addStretch(1)
        return page

    def _make_simple_page(self, title: str, desc: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel(title))
        card_layout.addWidget(QLabel(desc))
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _on_menu_changed(self, row: int) -> None:
        if 0 <= row < self.pages.count():
            self.pages.setCurrentIndex(row)

    def _refresh(self) -> None:
        logs = self.engine.drain_logs()
        if logs:
            self._append_logs(logs)

        status = self.engine.get_status()
        self.mode_label.setText(f"MODE: {status['mode']}")
        self.position_label.setText(f"보유 포지션: {status['positions']}")
        self.pnl_label.setText(f"오늘 손익: {status['daily_pnl_pct']:.2f}%")

    def _append_logs(self, logs: list[str]) -> None:
        for line in logs[-200:]:
            self.dashboard_log_preview.append(line)
            self.logs.append(line)

        for target in (self.dashboard_log_preview, self.logs):
            doc = target.document()
            while doc.blockCount() > 1000:
                cursor = target.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.select(cursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def _save_settings(self) -> None:
        payload = {
            "mode": self.mode_combo.currentText(),
            "max_buy_amount_krw": self.max_buy_spin.value(),
            "max_positions": self.max_positions_spin.value(),
            "min_ai_confidence": self.min_ai_spin.value(),
            "stop_loss_pct": self.stop_loss_spin.value(),
            "allow_new_buy_in_bear_market": self.bear_buy_check.isChecked(),
        }
        self.engine.update_settings(payload)
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다. 일부 항목은 즉시 반영됩니다.")

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
