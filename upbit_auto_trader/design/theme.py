from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(
        """
        QWidget { background: #f4f6f8; color: #1f2937; font-family: Pretendard, Apple SD Gothic Neo; }
        QFrame#Card { background: white; border-radius: 14px; }
        QPushButton#EmergencyStop { background: #ff3b30; color: white; font-weight: bold; border-radius: 12px; padding: 10px; }
        QLabel#Profit { color: #ef4444; font-size: 24px; font-weight: 700; }
        QLabel#Loss { color: #3b82f6; font-size: 24px; font-weight: 700; }
        QLabel#Accent { color: #22c55e; font-weight: 700; }
        """
    )
