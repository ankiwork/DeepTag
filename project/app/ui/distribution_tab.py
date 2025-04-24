import os
import json
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *


class DistributionTab(QWidget):
    """Вкладка для управления кадрами в подпроектах"""

    log_file = Path(__file__).parent.parent.parent / "logs" / "frames.log"
    projects_file = Path(__file__).parent.parent.parent / "data" / "projects.json"

    def __init__(self, projects_tab=None, subprojects_tab=None):
        super().__init__()
        self.projects = []
        self.filtered_projects = []
        self.current_project_index = -1
        self.current_project_data = None
        self.current_subproject_index = -1
        self._init_ui()
        self._load_projects()

        if projects_tab:
            projects_tab.projects_updated.connect(self._reload_projects)

        if subprojects_tab:
            subprojects_tab.subprojects_updated.connect(self._handle_subprojects_update)

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

        add_frames_btn = QPushButton("Добавить папку с кадрами")
        add_frames_btn.clicked.connect(self._add_frames_folder)  # type: ignore
        add_frames_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: 1px solid #0055AA;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077DD;
            }
        """)
        main_layout.addWidget(add_frames_btn)

        frames_columns = QHBoxLayout()

        self.unassigned_column = self._create_frame_column("Нераспределённые кадры")
        frames_columns.addWidget(self.unassigned_column)

        self.in_progress_column = self._create_frame_column("Кадры в работе")
        frames_columns.addWidget(self.in_progress_column)

        self.dataset_column = self._create_frame_column("Кадры в датасете")
        frames_columns.addWidget(self.dataset_column)

        main_layout.addLayout(frames_columns)
        self.setLayout(main_layout)

    def _handle_subprojects_update(self):
        """Обрабатывает обновление списка подпроектов"""
        if self.current_project_index >= 0:
            project_name = self.projects[self.current_project_index]["name"]
            project_file = Path(__file__).parent.parent.parent / "data" / f"{project_name}.json"

            try:
                if project_file.exists():
                    with open(project_file, 'r', encoding='utf-8') as f:
                        self.current_project_data = json.load(f)

                    self.subproject_combo.clear()
                    if "subprojects" in self.current_project_data:
                        for subproject in self.current_project_data["subprojects"]:
                            self.subproject_combo.addItem(subproject["name"])

                    if self.subproject_combo.count() > 0:
                        self._subproject_selected(0)
                    else:
                        self._clear_frames()
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Ошибка", "Не удалось прочитать данные проекта")

    def _create_top_panel(self) -> QFrame:
        """Создает верхнюю панель для выбора проекта и подпроекта"""
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFixedHeight(120)
        panel.setStyleSheet("background-color: #2D2D2D;")

        layout = QVBoxLayout(panel)

        project_layout = QHBoxLayout()
        project_label = QLabel("Проект:")
        project_label.setStyleSheet("color: white;")

        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._project_selected)  # type: ignore
        self.project_combo.setStyleSheet("""
            QComboBox {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
        """)

        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_combo, stretch=1)

        subproject_layout = QHBoxLayout()
        subproject_label = QLabel("Подпроект:")
        subproject_label.setStyleSheet("color: white;")

        self.subproject_combo = QComboBox()
        self.subproject_combo.currentIndexChanged.connect(self._subproject_selected)  # type: ignore
        self.subproject_combo.setStyleSheet(self.project_combo.styleSheet())

        subproject_layout.addWidget(subproject_label)
        subproject_layout.addWidget(self.subproject_combo, stretch=1)

        layout.addLayout(project_layout)
        layout.addLayout(subproject_layout)

        return panel

    @staticmethod
    def _create_frame_column(title: str) -> QWidget:
        """Создает колонку для кадров с заданным заголовком"""
        column = QWidget()
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(5)

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                padding: 5px;
                background-color: #3D3D3D;
                border-radius: 5px;
            }
        """)
        column_layout.addWidget(label)

        frame_list = QListWidget()
        frame_list.setStyleSheet("""
            QListWidget {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        frame_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        column_layout.addWidget(frame_list)

        return column

    @staticmethod
    def _create_folder_widget(folder_name: str, total_frames: int, marked_frames: int = 0) -> QWidget:
        """Создает виджет для отображения папки с кадрами"""
        widget = QWidget()
        widget.setStyleSheet("""
            background-color: #4D4D4D; 
            border-radius: 5px;
            padding: 5px;
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        name_label = QLabel(folder_name)
        name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        layout.addWidget(name_label)

        progress_layout = QHBoxLayout()

        progress_label = QLabel("Размечено:")
        progress_label.setStyleSheet("color: #AAAAAA;")

        progress_bar = QProgressBar()
        progress_bar.setMaximum(total_frames)
        progress_bar.setValue(marked_frames)
        progress_bar.setFormat(f"{marked_frames}/{total_frames}")
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0066CC;
            }
        """)

        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar, stretch=1)

        layout.addLayout(progress_layout)

        return widget

    def _load_projects(self) -> None:
        """Загружает список проектов из файла"""
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
                self._update_project_combo()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список проектов")

    def _update_project_combo(self):
        """Обновляет комбобокс с проектами"""
        self.project_combo.clear()
        for project in self.projects:
            self.project_combo.addItem(project["name"])

        if self.projects:
            self._project_selected(0)

    def _project_selected(self, index: int):
        """Обрабатывает выбор проекта"""
        if 0 <= index < len(self.projects):
            self.current_project_index = index
            project_name = self.projects[index]["name"]
            project_file = Path(__file__).parent.parent.parent / "data" / f"{project_name}.json"

            try:
                if project_file.exists():
                    with open(project_file, 'r', encoding='utf-8') as f:
                        self.current_project_data = json.load(f)

                    self.subproject_combo.clear()
                    if "subprojects" in self.current_project_data:
                        for subproject in self.current_project_data["subprojects"]:
                            self.subproject_combo.addItem(subproject["name"])

                    if self.subproject_combo.count() > 0:
                        self._subproject_selected(0)
                    else:
                        self._clear_frames()
                else:
                    self._clear_frames()
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные проекта")
                self._clear_frames()
        else:
            self._clear_frames()

    def _subproject_selected(self, index: int):
        """Обрабатывает выбор подпроекта"""
        if (self.current_project_data and
                "subprojects" in self.current_project_data and
                0 <= index < len(self.current_project_data["subprojects"])):

            self.current_subproject_index = index
            subproject_name = self.current_project_data["subprojects"][index]["name"]
            self._load_frames_for_subproject(subproject_name)
        else:
            self._clear_frames()

    def _load_frames_for_subproject(self, subproject_name: str):
        """Загружает кадры для выбранного подпроекта"""
        self._clear_frames()

        if "frames" not in self.current_project_data:
            self.current_project_data["frames"] = {}

        if subproject_name not in self.current_project_data["frames"]:
            self.current_project_data["frames"][subproject_name] = {
                "unassigned": {},
                "in_progress": {},
                "in_dataset": {}
            }

        frames_data = self.current_project_data["frames"][subproject_name]

        self._fill_column(self.unassigned_column, frames_data.get("unassigned", {}))
        self._fill_column(self.in_progress_column, frames_data.get("in_progress", {}))
        self._fill_column(self.dataset_column, frames_data.get("in_dataset", {}))

    def _fill_column(self, column: QWidget, frames_data: dict):
        """Заполняет колонку данными о кадрах"""
        frame_list = column.findChild(QListWidget)
        frame_list.clear()

        for folder_name, folder_data in frames_data.items():
            total = folder_data.get("total", 0)
            marked = folder_data.get("marked", 0)

            folder_widget = self._create_folder_widget(folder_name, total, marked)

            item = QListWidgetItem()
            item.setSizeHint(folder_widget.sizeHint())
            frame_list.addItem(item)
            frame_list.setItemWidget(item, folder_widget)

    def _clear_frames(self):
        """Очищает все колонки с кадрами"""
        for column in [self.unassigned_column, self.in_progress_column, self.dataset_column]:
            frame_list = column.findChild(QListWidget)
            frame_list.clear()

    def _add_frames_folder(self):
        """Добавляет новую папку с кадрами в подпроект"""
        if self.current_project_index == -1 or self.current_subproject_index == -1:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект и подпроект")
            return

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с кадрами",
            str(Path.home())
        )

        if not folder:
            return

        supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        frame_files = []

        for root, _, files in os.walk(folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_formats):
                    frame_files.append(os.path.join(root, file))

        if not frame_files:
            QMessageBox.warning(self, "Ошибка", "В выбранной папке нет поддерживаемых изображений")
            return

        subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
        folder_name = os.path.basename(folder)

        if "frames" not in self.current_project_data:
            self.current_project_data["frames"] = {}

        if subproject_name not in self.current_project_data["frames"]:
            self.current_project_data["frames"][subproject_name] = {
                "unassigned": {},
                "in_progress": {},
                "in_dataset": {}
            }

        if folder_name in self.current_project_data["frames"][subproject_name]["unassigned"]:
            reply = QMessageBox.question(
                self,
                "Папка уже добавлена",
                f"Папка '{folder_name}' уже добавлена в этот подпроект. Обновить список кадров?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.current_project_data["frames"][subproject_name]["unassigned"][folder_name] = {
            "path": folder,
            "total": len(frame_files),
            "marked": 0,
            "files": frame_files
        }

        self._save_project_data()
        self._load_frames_for_subproject(subproject_name)

        QMessageBox.information(
            self,
            "Успех",
            f"Добавлена папка '{folder_name}' с {len(frame_files)} кадрами в подпроект '{subproject_name}'"
        )

    def _save_project_data(self):
        """Сохраняет данные проекта"""
        if self.current_project_data and 0 <= self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]["name"]
            project_file = Path(__file__).parent.parent.parent / "data" / f"{project_name}.json"

            try:
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_project_data, f, indent=2, ensure_ascii=False)  # type: ignore
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить данные проекта")

    def _reload_projects(self):
        """Перезагружает список проектов"""
        self._load_projects()
