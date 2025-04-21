import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal

from project.app.utils.logger import setup_logger


class ProjectsTab(QWidget):
    """Вкладка для управления проектами с темным стилем"""

    projects_updated = pyqtSignal()
    data_file = Path(__file__).parent.parent.parent / "data" / "projects.json"
    log_file = Path(__file__).parent.parent.parent / "logs" / "projects.log"

    def __init__(self):
        super().__init__()
        self._ensure_data_dir_exists()
        self.logger = setup_logger("ProjectsTab", self.log_file)
        self.projects_data = []
        self._init_ui()
        self._load_projects()

    def _init_ui(self) -> None:
        """Инициализация интерфейса с темным стилем"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.Shape.StyledPanel)
        control_panel.setStyleSheet("background-color: #2D2D2D;")
        control_panel.setFixedHeight(80)

        control_layout = QHBoxLayout(control_panel)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Название проекта")
        self.project_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                font-size: 14px;
            }
        """)

        button_style = """
            QPushButton {
                background-color: #4D4D4D;
                color: white;
                border: 1px solid #555;
                padding: 5px 10px;
                min-width: 80px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5D5D5D;
            }
        """

        add_button = QPushButton("Добавить")
        add_button.setStyleSheet(button_style)
        add_button.clicked.connect(self._add_project)

        edit_button = QPushButton("Изменить")
        edit_button.setStyleSheet(button_style)
        edit_button.clicked.connect(self._edit_project)

        delete_button = QPushButton("Удалить")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #CC0000;
                color: white;
                border: 1px solid #AA0000;
                padding: 5px 10px;
                min-width: 80px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #DD0000;
            }
        """)
        delete_button.clicked.connect(self._delete_project)

        control_layout.addWidget(self.project_name_input, stretch=4)
        control_layout.addWidget(add_button, stretch=1)
        control_layout.addWidget(edit_button, stretch=1)
        control_layout.addWidget(delete_button, stretch=1)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название", "Дата создания", "Время создания"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #3D3D3D;
                color: white;
                gridline-color: #555;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #4D4D4D;
                color: white;
                padding: 5px;
                border: none;
                font-size: 14px;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def _ensure_data_dir_exists(self) -> None:
        """Создает директорию data/, если её нет"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_projects(self) -> None:
        """Загружает проекты из JSON-файла"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.projects_data = json.load(f)
                self.logger.info(f"Успешно загружено {len(self.projects_data)} проектов")
            else:
                self.projects_data = []
                self.logger.info("Файл проектов не найден, создан новый список")

            self._update_table()

        except Exception as e:
            error_msg = f"Не удалось загрузить проекты: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Ошибка", error_msg)

    def _save_projects(self) -> None:
        """Сохраняет проекты в JSON-файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects_data, f, indent=2, ensure_ascii=False)  # type: ignore
            self.logger.info(f"Успешно сохранено {len(self.projects_data)} проектов")
        except Exception as e:
            error_msg = f"Не удалось сохранить проекты: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, "Ошибка", error_msg)

    def _add_project(self) -> None:
        """Добавляет новый проект"""
        project_name = self.project_name_input.text().strip()

        if not project_name:
            QMessageBox.warning(self, "Ошибка", "Введите название проекта")
            return

        if any(p["name"] == project_name for p in self.projects_data):
            QMessageBox.warning(self, "Ошибка", "Проект с таким именем уже существует")
            return

        now = datetime.now()
        new_project = {
            "name": project_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }

        self.projects_data.append(new_project)
        self._update_table()
        self._save_projects()
        self.project_name_input.clear()
        self.logger.info(f"Добавлен новый проект: {project_name}")
        self.projects_updated.emit()  # type: ignore

    def _edit_project(self) -> None:
        """Изменяет название выбранного проекта"""
        project = self._get_selected_project()
        if not project:
            return

        old_name = project["name"]

        new_name, ok = QInputDialog.getText(
            self,
            "Изменение проекта",
            "Введите новое название проекта:",
            QLineEdit.EchoMode.Normal,
            old_name
        )

        if ok and new_name.strip():
            if new_name.strip() != old_name:
                if any(p["name"] == new_name.strip() for p in self.projects_data):
                    QMessageBox.warning(self, "Ошибка", "Проект с таким именем уже существует")
                    return

                project["name"] = new_name.strip()
                self._update_table()
                self._save_projects()
                self.logger.info(f"Изменение проекта с '{old_name}' на '{new_name.strip()}'")
                self.projects_updated.emit()  # type: ignore

    def _delete_project(self) -> None:
        """Удаляет выбранный проект после подтверждения"""
        project = self._get_selected_project()
        if not project:
            return

        project_name = project["name"]

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить проект '{project_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.projects_data.remove(project)
            self._update_table()
            self._save_projects()
            self.logger.info(f"Удален проект: {project_name}")
            self.projects_updated.emit()  # type: ignore

    def _update_table(self) -> None:
        """Обновляет таблицу проектов"""
        self.table.setRowCount(len(self.projects_data))

        for row, project in enumerate(self.projects_data):
            for col, key in enumerate(["name", "date", "time"]):
                item = QTableWidgetItem(project.get(key, ""))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

    def _get_selected_project(self) -> dict | None:
        """Возвращает выбранный проект или None"""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите проект")
            return None
        return self.projects_data[selected_row]
