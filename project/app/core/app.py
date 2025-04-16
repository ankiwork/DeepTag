from PyQt6.QtWidgets import QMainWindow, QTabWidget

from project.app.ui.tabs.projects_tab import ProjectsTab
from project.app.ui.tabs.settings_tab import SettingsTab


def _setup_tabs(tab_widget: QTabWidget) -> None:
    """Добавляет и настраивает вкладки.

    Args:
        tab_widget: Виджет для управления вкладками.
    """
    tab_widget.addTab(ProjectsTab(), "Проекты")
    tab_widget.addTab(SettingsTab(), "Настройки")


class MainWindow(QMainWindow):
    """Главное окно приложения с вкладками."""

    def __init__(self) -> None:
        """Инициализирует главное окно с настройками по умолчанию."""
        super().__init__()

        # Настройки окна
        self._setup_window()
        self._init_ui()

    def _setup_window(self) -> None:
        """Настраивает параметры главного окна."""
        self.setWindowTitle("DeepTag")
        self.setGeometry(100, 100, 800, 600)
        self.showMaximized()

    def _init_ui(self) -> None:
        """Инициализирует пользовательский интерфейс."""
        tab_widget = QTabWidget()

        # Добавление вкладок
        _setup_tabs(tab_widget)

        self.setCentralWidget(tab_widget)
