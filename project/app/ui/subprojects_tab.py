import json
from pathlib import Path
from PyQt6.QtCore import Qt
from datetime import datetime
from PyQt6.QtWidgets import *

from project.app.utils.logger import setup_logger


class SubprojectsTab(QWidget):
    """Вкладка для работы с подпроектами внутри проектов"""

    log_file = Path(__file__).parent.parent.parent / "logs" / "subprojects.log"
    projects_file = Path(__file__).parent.parent.parent / "data" / "projects.json"

    def __init__(self, projects_tab=None):
        super().__init__()
        self.logger = setup_logger("SubprojectsTab", self.log_file)
        self.projects = []
        self.filtered_projects = []
        self.current_project_index = -1
        self.current_project_data = None
        self._init_ui()
        self._load_projects()

        if projects_tab:
            projects_tab.projects_updated.connect(self._reload_projects)

    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        top_panel = self._create_top_panel()
        main_layout.addWidget(top_panel)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        self.bottom_panel = QTabWidget()
        self._setup_subprojects_ui()
        main_layout.addWidget(self.bottom_panel)

        self.setLayout(main_layout)
        self._update_navigation()

    def _create_top_panel(self) -> QFrame:
        """Создает верхнюю панель для выбора проекта"""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFixedHeight(120)
        panel.setStyleSheet("background-color: #2D2D2D;")

        layout = QVBoxLayout(panel)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск проекта...")
        self.search_input.textChanged.connect(self._filter_projects)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
        """)

        search_button = QPushButton("Найти")
        search_button.clicked.connect(self._search_project)
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #4D4D4D;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #5D5D5D;
            }
        """)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)

        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("←")
        self.prev_button.clicked.connect(self._prev_project)
        self.prev_button.setStyleSheet(search_button.styleSheet())

        self.project_label = QLabel("Выберите проект")
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.project_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        self.next_button = QPushButton("→")
        self.next_button.clicked.connect(self._next_project)
        self.next_button.setStyleSheet(search_button.styleSheet())

        self.open_button = QPushButton("Открыть проект")
        self.open_button.clicked.connect(self._open_project)
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: 1px solid #0055AA;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077DD;
            }
        """)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.project_label, stretch=1)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.open_button)

        layout.addLayout(search_layout)
        layout.addLayout(nav_layout)

        return panel

    def _setup_subprojects_ui(self):
        """Настраивает UI для управления подпроектами"""
        self.info_tab = QWidget()
        info_layout = QVBoxLayout(self.info_tab)

        self.project_info_label = QLabel("Выберите проект для просмотра информации")
        self.project_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.project_info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        info_layout.addWidget(self.project_info_label)

        self.subprojects_tab = QWidget()
        subprojects_layout = QVBoxLayout(self.subprojects_tab)

        control_layout = QHBoxLayout()

        self.subproject_name_input = QLineEdit()
        self.subproject_name_input.setPlaceholderText("Название подпроекта")
        self.subproject_name_input.setStyleSheet(self.search_input.styleSheet())

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self._add_subproject)
        add_button.setStyleSheet(self.open_button.styleSheet())

        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self._edit_subproject)
        edit_button.setStyleSheet(self.open_button.styleSheet())

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self._delete_subproject)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #CC0000;
                color: white;
                border: 1px solid #AA0000;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DD0000;
            }
        """)

        control_layout.addWidget(self.subproject_name_input, stretch=4)
        control_layout.addWidget(add_button, stretch=1)
        control_layout.addWidget(edit_button, stretch=1)
        control_layout.addWidget(delete_button, stretch=1)

        self.subprojects_table = QTableWidget()
        self.subprojects_table.setColumnCount(3)
        self.subprojects_table.setHorizontalHeaderLabels(["Название", "Дата создания", "Время создания"])
        self.subprojects_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.subprojects_table.verticalHeader().setVisible(False)
        self.subprojects_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.subprojects_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subprojects_table.setStyleSheet("""
            QTableWidget {
                background-color: #3D3D3D;
                color: white;
                gridline-color: #555;
            }
            QHeaderView::section {
                background-color: #4D4D4D;
                color: white;
                padding: 5px;
                border: none;
            }
        """)

        subprojects_layout.addLayout(control_layout)
        subprojects_layout.addWidget(self.subprojects_table)

        self.bottom_panel.addTab(self.info_tab, "Информация")
        self.bottom_panel.addTab(self.subprojects_tab, "Подпроекты")
        self.bottom_panel.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                background: #3D3D3D;
            }
            QTabBar::tab {
                background: #4D4D4D;
                color: white;
                padding: 8px;
                border: 1px solid #555;
            }
            QTabBar::tab:selected {
                background: #0066CC;
            }
        """)

    def _load_projects(self) -> None:
        """Загружает список проектов из файла"""
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
                self.filtered_projects = self.projects.copy()
                self.logger.info(f"Загружено {len(self.projects)} проектов")
                if self.projects:
                    self.current_project_index = 0
                    self._load_current_project_data()
            else:
                self.projects = []
                self.filtered_projects = []
                self.current_project_index = -1
                self.current_project_data = None
                self.logger.warning("Файл проектов не найден")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки проектов: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список проектов")

        self._update_navigation()

    def _load_current_project_data(self):
        """Загружает данные текущего выбранного проекта"""
        if 0 <= self.current_project_index < len(self.filtered_projects):
            project_name = self.filtered_projects[self.current_project_index]["name"]
            project_file = Path(__file__).parent.parent.parent / "data" / f"{project_name}.json"

            try:
                if project_file.exists():
                    with open(project_file, 'r', encoding='utf-8') as f:
                        self.current_project_data = json.load(f)
                    self.logger.info(f"Загружены данные проекта: {project_name}")
                else:
                    self.current_project_data = {
                        "name": project_name,
                        "subprojects": [],
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self._save_current_project_data()
                    self.logger.info(f"Созданы новые данные для проекта: {project_name}")
            except Exception as e:
                self.logger.error(f"Ошибка загрузки данных проекта {project_name}: {str(e)}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные проекта {project_name}")
        else:
            self.current_project_data = None

        self._update_subprojects_table()

    def _update_subprojects_table(self):
        """Обновляет таблицу подпроектов"""
        if self.current_project_data and "subprojects" in self.current_project_data:
            subprojects = self.current_project_data["subprojects"]
            self.subprojects_table.setRowCount(len(subprojects))

            for row, subproject in enumerate(subprojects):
                for col, key in enumerate(["name", "date", "time"]):
                    item = QTableWidgetItem(subproject.get(key, ""))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.subprojects_table.setItem(row, col, item)
        else:
            self.subprojects_table.setRowCount(0)

    def _save_current_project_data(self):
        """Сохраняет данные текущего проекта"""
        if self.current_project_data and 0 <= self.current_project_index < len(self.filtered_projects):
            project_name = self.filtered_projects[self.current_project_index]["name"]
            project_file = Path(__file__).parent.parent.parent / "data" / f"{project_name}.json"

            try:
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_project_data, f, indent=2, ensure_ascii=False)  # type: ignore
                self.logger.info(f"Сохранены данные проекта: {project_name}")
            except Exception as e:
                self.logger.error(f"Ошибка сохранения данных проекта {project_name}: {str(e)}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить данные проекта {project_name}")

    def _add_subproject(self):
        """Добавляет новый подпроект"""
        if not self.current_project_data:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект")
            return

        subproject_name = self.subproject_name_input.text().strip()
        if not subproject_name:
            QMessageBox.warning(self, "Ошибка", "Введите название подпроекта")
            return

        now = datetime.now()
        new_subproject = {
            "name": subproject_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }

        if "subprojects" not in self.current_project_data:
            self.current_project_data["subprojects"] = []

        if any(sp["name"] == subproject_name for sp in self.current_project_data["subprojects"]):
            QMessageBox.warning(self, "Ошибка", "Подпроект с таким именем уже существует")
            return

        self.current_project_data["subprojects"].append(new_subproject)
        self._update_subprojects_table()
        self._save_current_project_data()
        self.subproject_name_input.clear()

        self._update_project_info()

        self.logger.info(f"Добавлен подпроект '{subproject_name}' в проект '{self.current_project_data['name']}'")

    def _edit_subproject(self):
        """Редактирует выбранный подпроект"""
        if not self.current_project_data:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект")
            return

        selected_row = self.subprojects_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите подпроект для редактирования")
            return

        old_name = self.current_project_data["subprojects"][selected_row]["name"]

        new_name, ok = QInputDialog.getText(
            self,
            "Редактирование подпроекта",
            "Введите новое название подпроекта:",
            QLineEdit.EchoMode.Normal,
            old_name
        )

        if ok and new_name.strip():
            if new_name.strip() != old_name:
                if any(sp["name"] == new_name.strip() for sp in self.current_project_data["subprojects"]):
                    QMessageBox.warning(self, "Ошибка", "Подпроект с таким именем уже существует")
                    return

                self.current_project_data["subprojects"][selected_row]["name"] = new_name.strip()
                self._update_subprojects_table()
                self._save_current_project_data()
                self._update_project_info()
                self.logger.info(f"Подпроект '{old_name}' переименован в '{new_name.strip()}'")

    def _delete_subproject(self):
        """Удаляет выбранный подпроект"""
        if not self.current_project_data:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект")
            return

        selected_row = self.subprojects_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите подпроект для удаления")
            return

        subproject_name = self.current_project_data["subprojects"][selected_row]["name"]

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить подпроект '{subproject_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.current_project_data["subprojects"][selected_row]
            self._update_subprojects_table()
            self._save_current_project_data()
            self._update_project_info()
            self.logger.info(f"Удален подпроект '{subproject_name}'")

    def _update_project_info(self):
        """Обновляет информацию о проекте на вкладке информации"""
        if self.current_project_data:
            project_name = self.current_project_data["name"]
            created = self.current_project_data.get("created", "неизвестно")
            subprojects_count = len(self.current_project_data.get("subprojects", []))

            self.project_info_label.setText(
                f"Проект: {project_name}\n"
                f"Дата создания: {created}\n"
                f"Количество подпроектов: {subprojects_count}"
            )

    def _open_project(self):
        """Обрабатывает открытие выбранного проекта"""
        if 0 <= self.current_project_index < len(self.filtered_projects):
            project_name = self.filtered_projects[self.current_project_index]["name"]
            self.logger.info(f"Открытие проекта: {project_name}")
            self._load_current_project_data()
            self._update_project_info()
            self.bottom_panel.setCurrentIndex(0)

            QMessageBox.information(self, "Открытие проекта", f"Проект '{project_name}' успешно открыт")

    def _filter_projects(self, text: str) -> None:
        """Фильтрует проекты по введенному тексту"""
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
        """Ищет проект по точному совпадению"""
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
        """Переходит к предыдущему проекту"""
        if self.filtered_projects and self.current_project_index > 0:
            self.current_project_index -= 1
            self._update_navigation()

    def _next_project(self) -> None:
        """Переходит к следующему проекту"""
        if self.filtered_projects and self.current_project_index < len(self.filtered_projects) - 1:
            self.current_project_index += 1
            self._update_navigation()

    def _update_navigation(self) -> None:
        """Обновляет состояние навигации и отображение проекта"""
        if not self.filtered_projects:
            self.project_label.setText("Проекты не найдены")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.open_button.setEnabled(False)
            self.current_project_data = None
            self._update_subprojects_table()
            self.project_info_label.setText("Выберите проект для просмотра информации")
            return

        self.prev_button.setEnabled(self.current_project_index > 0)
        self.next_button.setEnabled(self.current_project_index < len(self.filtered_projects) - 1)
        self.open_button.setEnabled(self.current_project_index >= 0)

        if 0 <= self.current_project_index < len(self.filtered_projects):
            self._update_project_display(self.filtered_projects[self.current_project_index]["name"])

    def _update_project_display(self, project_name: str) -> None:
        """Обновляет отображение выбранного проекта"""
        self.project_label.setText(f"Выбран проект: {project_name}")

    def _reload_projects(self):
        """Перезагружает список проектов"""
        try:
            self._load_projects()
            self._filter_projects(self.search_input.text())
        except Exception as e:
            self.logger.error(f"Ошибка перезагрузки проектов: {str(e)}")
