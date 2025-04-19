import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import *
from project.app.utils.logger import setup_logger


class ProjectsTab(QWidget):
    """Вкладка для управления проектами с сохранением в JSON."""

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
        """Инициализация интерфейса."""
        main_layout = QVBoxLayout()

        self._setup_control_panel(main_layout)
        self._setup_projects_table(main_layout)
        self.setLayout(main_layout)

    def _ensure_data_dir_exists(self) -> None:
        """Создает директорию data/, если её нет."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def _setup_control_panel(self, layout: QVBoxLayout) -> None:
        """Настраивает панель управления проектами."""
        control_layout = QHBoxLayout()

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Название проекта")

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self._add_project)

        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self._edit_project)

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self._delete_project)

        control_layout.addWidget(self.project_name_input, stretch=4)
        control_layout.addWidget(add_button, stretch=1)
        control_layout.addWidget(edit_button, stretch=1)
        control_layout.addWidget(delete_button, stretch=1)

        layout.addLayout(control_layout)

    def _setup_projects_table(self, layout: QVBoxLayout) -> None:
        """Настраивает таблицу для отображения проектов."""
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название", "Дата создания", "Время создания"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.resizeColumnsToContents()

        layout.addWidget(self.table)

    def _load_projects(self) -> None:
        """Загружает проекты из JSON-файла."""
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
            QMessageBox.warning(self, "Ошибка", error_msg)

    def _save_projects(self) -> None:
        """Сохраняет проекты в JSON-файл."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Успешно сохранено {len(self.projects_data)} проектов")
        except Exception as e:
            error_msg = f"Не удалось сохранить проекты: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.warning(self, "Ошибка", error_msg)

    def _add_project(self) -> None:
        """Добавляет новый проект."""
        project_name = self.project_name_input.text().strip()

        if not project_name:
            error_msg = "Попытка добавить проект без названия"
            self.logger.warning(error_msg)
            QMessageBox.warning(self, "Ошибка", error_msg)
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

    def _edit_project(self) -> None:
        """Изменяет название выбранного проекта."""
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
                    error_msg = f"Попытка изменить проект на существующее имя: {new_name.strip()}"
                    self.logger.warning(error_msg)
                    QMessageBox.warning(self, "Ошибка", "Проект с таким именем уже существует")
                    return

                self.logger.info(f"Изменение проекта с '{old_name}' на '{new_name.strip()}'")
                project["name"] = new_name.strip()
                self._update_table()
                self._save_projects()
                QMessageBox.information(self, "Успех", "Название проекта изменено")

    def _delete_project(self) -> None:
        """Удаляет выбранный проект после подтверждения."""
        project = self._get_selected_project()
        if not project:
            return

        project_name = project["name"]

        confirm_dialog = QInputDialog(self)
        confirm_dialog.setWindowTitle("Подтверждение удаления")
        confirm_dialog.setLabelText(
            f"Вы действительно хотите удалить проект?\n"
            f"Для подтверждения введите название проекта:\n"
            f'"{project_name}"'
        )
        confirm_dialog.setTextValue("")
        confirm_dialog.setOkButtonText("Удалить")
        confirm_dialog.setCancelButtonText("Отмена")

        if confirm_dialog.exec() == QInputDialog.DialogCode.Accepted:
            if confirm_dialog.textValue() == project_name:
                self.projects_data.remove(project)
                self._update_table()
                self._save_projects()
                self.logger.info(f"Удален проект: {project_name}")
                QMessageBox.information(self, "Успех", "Проект успешно удален")
            else:
                error_msg = f"Неверное подтверждение удаления для проекта {project_name}"
                self.logger.warning(error_msg)
                QMessageBox.warning(self, "Ошибка", "Название проекта не совпадает")

    def _update_table(self) -> None:
        """Обновляет данные в таблице."""
        self.table.setRowCount(len(self.projects_data))

        for row, project in enumerate(self.projects_data):
            self.table.setItem(row, 0, QTableWidgetItem(project.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(project.get("date", "")))
            self.table.setItem(row, 2, QTableWidgetItem(project.get("time", "")))

    def _get_selected_project(self) -> dict | None:
        """Возвращает выбранный проект или None, если ничего не выбрано."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите проект")
            return None
        return self.projects_data[selected_row]
