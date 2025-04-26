from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from project.app.utils.logger import setup_logger


class SettingsTab(QWidget):
    """Пустая вкладка настроек для последующего наполнения"""

    def __init__(self):
        super().__init__()
        self.log_file = Path(__file__).parent.parent.parent / "logs" / "settings.log"
        self.logger = setup_logger("SettingsTab", self.log_file)
        self.logger.info("Инициализация пустой вкладки настроек")
        self._init_ui()

    def _init_ui(self) -> None:
        """Инициализация базового интерфейса"""
        layout = QVBoxLayout()
        self.setLayout(layout)
