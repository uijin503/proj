from PySide6.QtCore import QThread


class EngineThread(QThread):
    """Runs the trading engine in a dedicated thread to keep UI responsive."""

    def __init__(self, engine):
        super().__init__()
        self._engine = engine

    def run(self) -> None:
        self._engine.run_forever()

    def stop(self) -> None:
        self._engine.stop()
        self.quit()
        self.wait(5000)
