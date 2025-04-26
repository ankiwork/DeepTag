import os
import json
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QMimeData, QPoint, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap, QPainter


class DistributionTab(QWidget):
    """Вкладка для управления кадрами в подпроектах"""

    folders_updated = pyqtSignal()

    log_file = Path(__file__).parent.parent.parent / "logs" / "frames.log"
    projects_file = Path(__file__).parent.parent.parent / "data" / "projects.json"

    def __init__(self, projects_tab=None, subprojects_tab=None):
        super().__init__()
        self.projects = []
        self.filtered_projects = []
        self.current_project_index = -1
        self.current_project_data = None
        self.current_subproject_index = -1
        self.drag_start_position = QPoint()
        self.dragged_item = None
        self.dragged_widget = None
        self.selected_folder = None
        self.selected_column = None
        self._init_ui()
        self._load_projects()

        if projects_tab:
            projects_tab.projects_updated.connect(self._reload_projects)

        if subprojects_tab:
            subprojects_tab.subprojects_updated.connect(self._handle_subprojects_update)

    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        top_panel = self._create_top_panel()
        main_layout.addWidget(top_panel)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        self.folder_control_panel = QWidget()
        folder_control_layout = QHBoxLayout(self.folder_control_panel)
        folder_control_layout.setContentsMargins(0, 0, 0, 0)

        self.rename_btn = QPushButton("Переименовать папку")
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: #AAAAAA;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:enabled {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:enabled:hover {
                background-color: #45a049;
            }
        """)
        self.rename_btn.setEnabled(False)
        self.rename_btn.clicked.connect(self._rename_folder)

        self.delete_btn = QPushButton("Удалить папку")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: #AAAAAA;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:enabled {
                background-color: #f44336;
                color: white;
            }
            QPushButton:enabled:hover {
                background-color: #d32f2f;
            }
        """)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_folder)

        folder_control_layout.addWidget(self.rename_btn)
        folder_control_layout.addWidget(self.delete_btn)
        folder_control_layout.addStretch()

        main_layout.addWidget(self.folder_control_panel)

        add_frames_btn = QPushButton("Добавить папку с кадрами")
        add_frames_btn.clicked.connect(self._add_frames_folder)
        add_frames_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: 1px solid #0055AA;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0077DD;
            }
        """)
        main_layout.addWidget(add_frames_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        frames_columns = QHBoxLayout()
        frames_columns.setContentsMargins(5, 5, 5, 5)
        frames_columns.setSpacing(15)

        self.unassigned_column = self._create_frame_column("Нераспределённые кадры", "unassigned")
        frames_columns.addWidget(self.unassigned_column, stretch=1)

        self.in_progress_column = self._create_frame_column("Кадры в работе", "in_progress")
        frames_columns.addWidget(self.in_progress_column, stretch=1)

        self.dataset_column = self._create_frame_column("Кадры в датасете", "in_dataset")
        frames_columns.addWidget(self.dataset_column, stretch=1)

        main_layout.addLayout(frames_columns)
        self.setLayout(main_layout)

        self.setMouseTracking(True)
        self.mousePressEvent = self._clear_selection

    def _clear_selection(self, event):
        """Очищает выделение при клике по пустому месту"""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_widget = self.childAt(event.pos())
            if not clicked_widget or not isinstance(clicked_widget, (QListWidget, QPushButton, QComboBox)):
                self._deselect_all()

    def _deselect_all(self):
        """Снимает выделение со всех элементов"""
        for column in [self.unassigned_column, self.in_progress_column, self.dataset_column]:
            frame_list = column.findChild(QListWidget)
            frame_list.clearSelection()

        self.selected_folder = None
        self.selected_column = None
        self.rename_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _create_frame_column(self, title: str, column_type: str) -> QWidget:
        """Создает колонку для кадров с заданным заголовком"""
        column = QWidget()
        column.setObjectName(column_type)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(5, 5, 5, 5)
        column_layout.setSpacing(10)

        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                padding: 8px;
                background-color: #3D3D3D;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        column_layout.addWidget(label)

        frame_list = QListWidget()
        frame_list.setObjectName(f"list_{column_type}")
        frame_list.setStyleSheet("""
            QListWidget {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                margin-bottom: 8px;
            }
            QListWidget::item:last {
                margin-bottom: 0;
            }
        """)
        frame_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        frame_list.setDragEnabled(True)
        frame_list.setAcceptDrops(True)
        frame_list.setDropIndicatorShown(True)
        frame_list.setDragDropMode(QListWidget.DragDropMode.DragDrop)

        frame_list.mousePressEvent = lambda event: self._mouse_press_event(frame_list, event)
        frame_list.mouseMoveEvent = lambda event: self._mouse_move_event(frame_list, event)
        frame_list.dragEnterEvent = lambda event: self._drag_enter_event(frame_list, event)
        frame_list.dragMoveEvent = lambda event: self._drag_move_event(frame_list, event)
        frame_list.dropEvent = lambda event: self._drop_event(frame_list, event)
        frame_list.dragLeaveEvent = lambda event: self._drag_leave_event(frame_list, event)
        frame_list.itemClicked.connect(lambda item: self._folder_selected(frame_list, item))

        column_layout.addWidget(frame_list)
        return column

    def _folder_selected(self, list_widget: QListWidget, item: QListWidgetItem):
        """Обрабатывает выбор папки"""
        for column in [self.unassigned_column, self.in_progress_column, self.dataset_column]:
            if column.findChild(QListWidget) != list_widget:
                column.findChild(QListWidget).clearSelection()

        self.selected_folder = list_widget.itemWidget(item).findChild(QLabel).text()
        self.selected_column = list_widget.parent().objectName()
        self.rename_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def _rename_folder(self):
        """Переименовывает выбранную папку"""
        if not self.selected_folder or not self.selected_column:
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Переименовать папку",
            "Введите новое имя папки:",
            text=self.selected_folder
        )

        if ok and new_name and new_name != self.selected_folder:
            subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
            frames_data = self.current_project_data["frames"][subproject_name]

            if new_name in frames_data[self.selected_column]:
                QMessageBox.warning(self, "Ошибка", "Папка с таким именем уже существует")
                return

            frames_data[self.selected_column][new_name] = frames_data[self.selected_column].pop(self.selected_folder)
            self._save_project_data()
            self._load_frames_for_subproject(subproject_name)
            self._deselect_all()
            self.folders_updated.emit()  # type: ignore

    def _delete_folder(self):
        """Удаляет выбранную папку"""
        if not self.selected_folder or not self.selected_column:
            return

        reply = QMessageBox.question(
            self,
            "Удаление папки",
            f"Вы уверены, что хотите удалить папку '{self.selected_folder}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
            frames_data = self.current_project_data["frames"][subproject_name]

            del frames_data[self.selected_column][self.selected_folder]
            self._save_project_data()
            self._load_frames_for_subproject(subproject_name)
            self._deselect_all()
            self.folders_updated.emit()  # type: ignore

    def _mouse_press_event(self, list_widget: QListWidget, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = list_widget.itemAt(event.pos())
            if item:
                self.drag_start_position = event.pos()
                self.dragged_item = item
                self.dragged_widget = list_widget.itemWidget(item)
        QListWidget.mousePressEvent(list_widget, event)

    def _mouse_move_event(self, list_widget: QListWidget, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or not self.dragged_item:
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(list_widget)
        mime_data = QMimeData()
        mime_data.setProperty("source_column", list_widget.parent().objectName())
        mime_data.setProperty("folder_name", self.dragged_widget.findChild(QLabel).text())
        drag.setMimeData(mime_data)

        pixmap = QPixmap(self.dragged_item.sizeHint())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.dragged_widget.render(painter)
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos() - self.drag_start_position)

        drag.exec(Qt.DropAction.MoveAction)

    @staticmethod
    def _drag_enter_event(list_widget: QListWidget, event):
        if event.mimeData():
            event.acceptProposedAction()
            list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #3D3D3D;
                    color: white;
                    border: 2px dashed #0066CC;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

    @staticmethod
    def _drag_move_event(list_widget: QListWidget, event):
        if event.mimeData():
            event.acceptProposedAction()

    @staticmethod
    def _drag_leave_event(list_widget: QListWidget, event):
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
        """)

    def _drop_event(self, target_list: QListWidget, event):
        target_list.setStyleSheet("""
            QListWidget {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        mime_data = event.mimeData()
        if not mime_data:
            return

        source_column = mime_data.property("source_column")
        folder_name = mime_data.property("folder_name")

        if not source_column or not folder_name:
            return

        target_column = target_list.parent().objectName()

        if source_column == target_column:
            return

        subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
        frames_data = self.current_project_data["frames"][subproject_name]
        folder_data = frames_data[source_column][folder_name]
        total_frames = folder_data["total"]

        target_frames = frames_data.get(target_column, {})
        base_name = folder_name
        part_num = 1

        while f"{base_name}_part_{part_num}" in target_frames:
            part_num += 1

        dialog = TransferDialog(folder_name, total_frames,
                                base_name=f"{base_name}_part_{part_num}" if part_num > 1 else base_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, frames_to_transfer = dialog.get_values()

            if new_name in frames_data.get(target_column, {}):
                base_new_name = new_name.split("_part_")[0] if "_part_" in new_name else new_name
                part_num = 1
                while f"{base_new_name}_part_{part_num}" in frames_data.get(target_column, {}):
                    part_num += 1
                new_name = f"{base_new_name}_part_{part_num}"

            self._transfer_frames(source_column, target_column, folder_name, new_name, frames_to_transfer)

        event.acceptProposedAction()
    def _transfer_frames(self, source_column: str, target_column: str, old_name: str, new_name: str,
                         frames_to_transfer: int):
        if not self.current_project_data or self.current_project_index == -1 or self.current_subproject_index == -1:
            return

        subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
        frames_data = self.current_project_data["frames"][subproject_name]

        if old_name not in frames_data[source_column]:
            return

        folder_data = frames_data[source_column][old_name]
        total_frames = folder_data["total"]
        marked_frames = folder_data["marked"]
        files = folder_data["files"]

        if frames_to_transfer == total_frames:
            frames_data[target_column][new_name] = {
                "path": folder_data["path"],
                "total": total_frames,
                "marked": marked_frames,
                "files": files.copy()
            }
            del frames_data[source_column][old_name]
        else:
            transferred_files = files[:frames_to_transfer]
            remaining_files = files[frames_to_transfer:]

            frames_data[target_column][new_name] = {
                "path": folder_data["path"],
                "total": frames_to_transfer,
                "marked": 0,
                "files": transferred_files
            }

            frames_data[source_column][old_name] = {
                "path": folder_data["path"],
                "total": len(remaining_files),
                "marked": marked_frames,
                "files": remaining_files
            }

        self._save_project_data()
        self._load_frames_for_subproject(subproject_name)
        self.folders_updated.emit()  # type: ignore


    @staticmethod
    def _create_folder_widget(folder_name: str, total_frames: int, marked_frames: int = 0) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #4D4D4D; 
                border-radius: 5px;
                padding: 8px;
                margin: 3px;
            }
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
        progress_layout.setContentsMargins(0, 0, 0, 0)

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
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0066CC;
                border-radius: 2px;
            }
        """)

        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar, stretch=1)
        layout.addLayout(progress_layout)

        return widget

    def _handle_subprojects_update(self):
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
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        panel.setFixedHeight(120)
        panel.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        project_layout = QHBoxLayout()
        project_layout.setSpacing(10)
        project_label = QLabel("Проект:")
        project_label.setStyleSheet("color: white;")

        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._project_selected)
        self.project_combo.setStyleSheet("""
            QComboBox {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
                min-width: 200px;
            }
        """)

        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_combo, stretch=1)

        subproject_layout = QHBoxLayout()
        subproject_layout.setSpacing(10)
        subproject_label = QLabel("Подпроект:")
        subproject_label.setStyleSheet("color: white;")

        self.subproject_combo = QComboBox()
        self.subproject_combo.currentIndexChanged.connect(self._subproject_selected)
        self.subproject_combo.setStyleSheet(self.project_combo.styleSheet())

        subproject_layout.addWidget(subproject_label)
        subproject_layout.addWidget(self.subproject_combo, stretch=1)

        layout.addLayout(project_layout)
        layout.addLayout(subproject_layout)

        return panel

    def _load_projects(self) -> None:
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
                self._update_project_combo()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список проектов")

    def _update_project_combo(self):
        self.project_combo.clear()
        for project in self.projects:
            self.project_combo.addItem(project["name"])

        if self.projects:
            self._project_selected(0)

    def _project_selected(self, index: int):
        """Обрабатывает выбор проекта"""
        self._deselect_all()

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
        self._deselect_all()

        if (self.current_project_data and
                "subprojects" in self.current_project_data and
                0 <= index < len(self.current_project_data["subprojects"])):

            self.current_subproject_index = index
            subproject_name = self.current_project_data["subprojects"][index]["name"]
            self._load_frames_for_subproject(subproject_name)
        else:
            self._clear_frames()

    def _load_frames_for_subproject(self, subproject_name: str):
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
        for column in [self.unassigned_column, self.in_progress_column, self.dataset_column]:
            frame_list = column.findChild(QListWidget)
            frame_list.clear()

    def _add_frames_folder(self):
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
        self.folders_updated.emit()  # type: ignore

        QMessageBox.information(
            self,
            "Успех",
            f"Добавлена папка '{folder_name}' с {len(frame_files)} кадрами в подпроект '{subproject_name}'"
        )

    def _save_project_data(self):
        if self.current_project_data and 0 <= self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]["name"]
            project_file = Path(__file__).parent.parent.parent / "data" / f"{project_name}.json"

            try:
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_project_data, f, indent=2, ensure_ascii=False)  # type: ignore
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить данные проекта")

    def _reload_projects(self):
        self._load_projects()


class TransferDialog(QDialog):
    """Диалог для подтверждения переноса кадров"""

    def __init__(self, folder_name: str, total_frames: int, base_name=None):
        super().__init__()
        self.folder_name = folder_name
        self.total_frames = total_frames
        self.base_name = base_name if base_name else folder_name
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Перенос кадров")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        info_label = QLabel(f"Перенос папки: {self.folder_name}")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        self.frames_slider = QSlider(Qt.Orientation.Horizontal)
        self.frames_slider.setRange(1, self.total_frames)
        self.frames_slider.setValue(self.total_frames)
        layout.addWidget(self.frames_slider)

        self.frames_count = QLabel(f"{self.total_frames} кадров")
        self.frames_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.frames_count)

        self.new_name_edit = QLineEdit(self.base_name)
        self.new_name_edit.setPlaceholderText("Новое название папки")
        layout.addWidget(self.new_name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.frames_slider.valueChanged.connect(self._update_frames_count)
        self.setLayout(layout)

    def _update_frames_count(self, value):
        self.frames_count.setText(f"{value} кадров")

    def get_values(self):
        if self.frames_slider.value() == self.total_frames:
            return self.new_name_edit.text() or self.folder_name, self.total_frames
        else:
            return self.new_name_edit.text() or f"{self.folder_name}_part", self.frames_slider.value()
