from PyQt6.QtWidgets import QMainWindow, QTabWidget

from project.app.ui.projects_tab import ProjectsTab
from project.app.ui.settings_tab import SettingsTab
from project.app.ui.subprojects_tab import SubprojectsTab
from project.app.ui.distribution_tab import DistributionTab


def _setup_tabs(tab_widget: QTabWidget) -> None:
    """Добавляет и настраивает вкладки"""
    projects_tab = ProjectsTab()
    subprojects_tab = SubprojectsTab(projects_tab)
    distribution_tab = DistributionTab(projects_tab, subprojects_tab)

    tab_widget.addTab(projects_tab, "Проекты")
    tab_widget.addTab(subprojects_tab, "Подпроекты")
    tab_widget.addTab(distribution_tab, "Распределение")
    tab_widget.addTab(SettingsTab(), "Настройки")


class MainWindow(QMainWindow):
    """Главное окно приложения с вкладками"""

    def __init__(self) -> None:
        super().__init__()
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
        _setup_tabs(tab_widget)
        self.setCentralWidget(tab_widget)
