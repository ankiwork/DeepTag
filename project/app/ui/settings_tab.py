from PyQt6.QtWidgets import *


class SettingsTab(QWidget):
    """Пустая вкладка настроек."""
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        """Инициализация пустого интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
