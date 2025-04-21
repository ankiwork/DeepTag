import json
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from project.app.utils.logger import setup_logger


class SubprojectsTab(QWidget):
    """Вкладка для работы с подпроектами"""

    log_file = Path(__file__).parent.parent.parent / "logs" / "subprojects.log"
    projects_file = Path(__file__).parent.parent.parent / "data" / "projects.json"

    def __init__(self, projects_tab=None):
        super().__init__()
        self.logger = setup_logger("SubprojectsTab", self.log_file)
        self.projects = []
        self.filtered_projects = []
        self.current_project_index = -1
        self._init_ui()
        self._load_projects()

        if projects_tab:
            projects_tab.projects_updated.connect(self._reload_projects)

    def _init_ui(self) -> None:
        """Инициализация интерфейса с разделением на две части."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        top_panel = QFrame()
        top_panel.setFrameShape(QFrame.Shape.StyledPanel)
        top_panel.setFixedHeight(120)

        top_layout = QVBoxLayout(top_panel)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск проекта...")
        self.search_input.textChanged.connect(self._filter_projects)
        search_button = QPushButton("Найти")
        search_button.clicked.connect(self._search_project)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)

        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("←")
        self.prev_button.clicked.connect(self._prev_project)
        self.project_label = QLabel("Выберите проект")
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QPushButton("→")
        self.next_button.clicked.connect(self._next_project)
        self.open_button = QPushButton("Открыть проект")
        self.open_button.clicked.connect(self._open_project)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.project_label, stretch=1)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.open_button)

        top_layout.addLayout(search_layout)
        top_layout.addLayout(nav_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        bottom_panel = QFrame()
        bottom_panel.setFrameShape(QFrame.Shape.StyledPanel)

        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.addWidget(QLabel("Содержимое проекта будет отображаться здесь"))

        main_layout.addWidget(top_panel)
        main_layout.addWidget(separator)
        main_layout.addWidget(bottom_panel)

        self.setLayout(main_layout)
        self._update_navigation()

    def _load_projects(self) -> None:
        """Загружает список проектов из файла."""
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
                self.filtered_projects = self.projects.copy()
                self.logger.info(f"Загружено {len(self.projects)} проектов")
                if self.projects:
                    self.current_project_index = 0
            else:
                self.projects = []
                self.filtered_projects = []
                self.current_project_index = -1
                self.logger.warning("Файл проектов не найден")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки проектов: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список проектов")

        self._update_navigation()

    def _filter_projects(self, text: str) -> None:
        """Фильтрует проекты по введенному тексту."""
        if not text:
            self.filtered_projects = self.projects.copy()
        else:
            self.filtered_projects = [
                p for p in self.projects
                if text.lower() in p["name"].lower()
            ]

        if self.filtered_projects:
            self.current_project_index = 0
        else:
            self.current_project_index = -1

        self._update_navigation()

    def _search_project(self) -> None:
        """Ищет проект по точному совпадению."""
        search_text = self.search_input.text().strip()
        if not search_text:
            self._filter_projects("")
            return

        for i, project in enumerate(self.filtered_projects):
            if project["name"].lower() == search_text.lower():
                self.current_project_index = i
                self._update_navigation()
                return

        QMessageBox.information(self, "Поиск", "Проект не найден")

    def _prev_project(self) -> None:
        """Переходит к предыдущему проекту."""
        if self.filtered_projects and self.current_project_index > 0:
            self.current_project_index -= 1
            self._update_navigation()

    def _next_project(self) -> None:
        """Переходит к следующему проекту."""
        if self.filtered_projects and self.current_project_index < len(self.filtered_projects) - 1:
            self.current_project_index += 1
            self._update_navigation()

    def _open_project(self) -> None:
        """Обрабатывает открытие выбранного проекта."""
        if 0 <= self.current_project_index < len(self.filtered_projects):
            project_name = self.filtered_projects[self.current_project_index]["name"]
            self.logger.info(f"Открытие проекта: {project_name}")
            QMessageBox.information(self, "Открытие проекта", f"Проект '{project_name}' будет открыт")

    def _update_navigation(self) -> None:
        """Обновляет состояние навигации и отображение проекта."""
        if not self.filtered_projects:
            self.project_label.setText("Проекты не найдены")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.open_button.setEnabled(False)
            return

        self.prev_button.setEnabled(self.current_project_index > 0)
        self.next_button.setEnabled(self.current_project_index < len(self.filtered_projects) - 1)
        self.open_button.setEnabled(self.current_project_index >= 0)

        if 0 <= self.current_project_index < len(self.filtered_projects):
            self._update_project_display(self.filtered_projects[self.current_project_index]["name"])

    def _update_project_display(self, project_name: str) -> None:
        """Обновляет отображение выбранного проекта."""
        self.project_label.setText(f"Выбран проект: {project_name}")

    def _reload_projects(self):
        """Перезагружает список проектов"""
        self._load_projects()
        self._filter_projects(self.search_input.text())
