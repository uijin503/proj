import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.ui.main_window import MainWindow
from core.engine import TradingEngine
from core.threading import EngineThread
from design.theme import apply_theme


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> int:
    configure_logging()
    app = QApplication(sys.argv)
    apply_theme(app)

    engine = TradingEngine()
    thread = EngineThread(engine=engine)
    window = MainWindow(engine=engine, engine_thread=thread)

    window.show()
    thread.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
