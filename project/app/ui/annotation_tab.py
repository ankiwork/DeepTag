import json
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QMouseEvent


class AnnotationTab(QWidget):
    """Вкладка для разметки изображений"""

    def __init__(self, projects_tab=None, subprojects_tab=None, distribution_tab=None):
        super().__init__()
        self.projects = []
        self.current_project_index = -1
        self.current_project_data = None
        self.current_subproject_index = -1
        self.current_image_index = 0
        self.image_files = []
        self._init_ui()
        self._load_projects()

        if projects_tab:
            projects_tab.projects_updated.connect(self._reload_projects)

        if subprojects_tab:
            subprojects_tab.subprojects_updated.connect(self._handle_subprojects_update)

        if distribution_tab:
            distribution_tab.folders_updated.connect(self._reload_folders)

    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        project_panel = QFrame()
        project_panel.setFrameShape(QFrame.Shape.StyledPanel)
        project_panel.setStyleSheet("background-color: #2D2D2D;")
        project_layout = QVBoxLayout(project_panel)

        project_combo_layout = QHBoxLayout()
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
            }
        """)

        project_combo_layout.addWidget(project_label)
        project_combo_layout.addWidget(self.project_combo)
        project_layout.addLayout(project_combo_layout)

        subproject_combo_layout = QHBoxLayout()
        subproject_label = QLabel("Подпроект:")
        subproject_label.setStyleSheet("color: white;")

        self.subproject_combo = QComboBox()
        self.subproject_combo.currentIndexChanged.connect(self._subproject_selected)
        self.subproject_combo.setStyleSheet(self.project_combo.styleSheet())

        subproject_combo_layout.addWidget(subproject_label)
        subproject_combo_layout.addWidget(self.subproject_combo)
        project_layout.addLayout(subproject_combo_layout)

        left_layout.addWidget(project_panel)

        self.folders_list = QListWidget()
        self.folders_list.setStyleSheet("""
            QListWidget {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        self.folders_list.itemClicked.connect(self._folder_selected)
        left_layout.addWidget(self.folders_list)

        main_layout.addWidget(left_panel)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)

        nav_panel = QWidget()
        nav_layout = QHBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        self.prev_btn = QPushButton("← Назад")
        self.prev_btn.clicked.connect(self._prev_image)
        self.prev_btn.setStyleSheet("""
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

        self.image_counter = QLabel("0/0")
        self.image_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_counter.setStyleSheet("color: white; font-weight: bold;")

        self.next_btn = QPushButton("Вперед →")
        self.next_btn.clicked.connect(self._next_image)
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_counter, stretch=1)
        nav_layout.addWidget(self.next_btn)

        center_layout.addWidget(nav_panel)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
                QLabel {
                    background-color: #2D2D2D;
                    border: 1px solid #555;
                }
            """)
        self.image_label.setMinimumSize(200, 200)
        center_layout.addWidget(self.image_label, stretch=1)

        main_layout.addWidget(center_panel, stretch=1)

        right_panel = QWidget()
        right_panel.setFixedWidth(250)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        tools_label = QLabel("Инструменты разметки")
        tools_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                padding: 8px;
                background-color: #3D3D3D;
                border-radius: 5px;
            }
        """)
        right_layout.addWidget(tools_label)

        self.rect_tool = QPushButton("Прямоугольник")
        self.rect_tool.setStyleSheet(self.prev_btn.styleSheet())
        right_layout.addWidget(self.rect_tool)

        self.polygon_tool = QPushButton("Полигон")
        self.polygon_tool.setStyleSheet(self.prev_btn.styleSheet())
        right_layout.addWidget(self.polygon_tool)

        self.point_tool = QPushButton("Точка")
        self.point_tool.setStyleSheet(self.prev_btn.styleSheet())
        right_layout.addWidget(self.point_tool)

        self.save_btn = QPushButton("Сохранить разметку")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        right_layout.addWidget(self.save_btn)

        right_layout.addStretch()
        main_layout.addWidget(right_panel)

        self.setLayout(main_layout)
        self._update_buttons_state()

        self.folders_list.setStyleSheet("""
                QListWidget {
                    background-color: #2D2D2D;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 3px;
                }
                QListWidget::item {
                    margin: 3px;
                    border: none;
                }
                QListWidget::item:selected {
                    background: transparent;
                }
            """)
        self.folders_list.setSpacing(3)

        self._current_scale = 1.0
        self._base_pixmap = None
        self._min_scale = 0.1
        self._max_scale = 3.0
        self._zoom_step = 0.1
        self._offset = QPoint(0, 0)
        self._drag_start_pos = QPoint()
        self._is_dragging = False

    def _reload_folders(self):
        if (self.current_project_data and
                0 <= self.current_subproject_index < len(self.current_project_data["subprojects"])):
            subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
            self._load_folders_for_subproject(subproject_name)

    def _load_projects(self) -> None:
        projects_file = Path(__file__).parent.parent.parent / "data" / "projects.json"
        try:
            if projects_file.exists():
                with open(projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
                self._update_project_combo()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список проектов")

    def _update_project_combo(self):
        self.project_combo.clear()
        for project in self.projects:
            self.project_combo.addItem(project["name"])

    def _project_selected(self, index: int):
        self._clear_selection()
        self.current_project_index = index

        if 0 <= index < len(self.projects):
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
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные проекта")

    def _subproject_selected(self, index: int):
        self._clear_selection()
        self.current_subproject_index = index

        if (self.current_project_data and
                "subprojects" in self.current_project_data and
                0 <= index < len(self.current_project_data["subprojects"])):
            subproject_name = self.current_project_data["subprojects"][index]["name"]
            self._load_folders_for_subproject(subproject_name)

    def _load_folders_for_subproject(self, subproject_name: str):
        self.folders_list.clear()
        self.image_files = []
        self.current_image_index = 0
        self._update_buttons_state()
        self._clear_image()

        if not self.current_project_data or "frames" not in self.current_project_data:
            return

        if subproject_name not in self.current_project_data["frames"]:
            return

        frames_data = self.current_project_data["frames"][subproject_name]
        in_progress_folders = frames_data.get("in_progress", {})

        if not in_progress_folders:
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setContentsMargins(10, 20, 10, 20)

            empty_label = QLabel("Нет папок в работе")
            empty_label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                    font-style: italic;
                    font-size: 13px;
                }
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_label)

            item = QListWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)
            self.folders_list.addItem(item)
            self.folders_list.setItemWidget(item, empty_widget)
            return

        for folder_name, folder_data in sorted(in_progress_folders.items()):
            folder_widget = QWidget()
            folder_widget.setStyleSheet("""
                QWidget {
                    background-color: #3D3D3D;
                    border: 1px solid #555;
                    border-radius: 5px;
                    margin: 3px;
                }
                QWidget:hover {
                    background-color: #4D4D4D;
                    border: 1px solid #666;
                }
            """)

            folder_layout = QVBoxLayout(folder_widget)
            folder_layout.setContentsMargins(8, 8, 8, 8)
            folder_layout.setSpacing(5)

            name_label = QLabel(folder_name)
            name_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    padding-bottom: 3px;
                }
            """)
            folder_layout.addWidget(name_label)

            info_layout = QHBoxLayout()

            count_label = QLabel(f"Кадров: {folder_data.get('total', 0)}")
            count_label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                    font-size: 12px;
                }
            """)
            info_layout.addWidget(count_label)

            folder_layout.addLayout(info_layout)

            item = QListWidgetItem()
            item.setSizeHint(folder_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, folder_name)

            self.folders_list.addItem(item)
            self.folders_list.setItemWidget(item, folder_widget)

    def _folder_selected(self, item):
        if (not self.current_project_data or
                self.current_project_index == -1 or
                self.current_subproject_index == -1):
            return

        folder_name = item.data(Qt.ItemDataRole.UserRole)
        if not folder_name:
            return

        subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
        frames_data = self.current_project_data["frames"][subproject_name]

        if folder_name not in frames_data.get("in_progress", {}):
            return

        folder_data = frames_data["in_progress"][folder_name]
        self.image_files = folder_data.get("files", [])
        self.current_image_index = 0
        self._update_buttons_state()
        self._update_image_counter()

        if self.image_files:
            self._show_current_image()
        else:
            self._clear_image()

    def _show_current_image(self):
        if not self.image_files or self.current_image_index < 0 or self.current_image_index >= len(self.image_files):
            self._clear_image()
            return

        image_path = self.image_files[self.current_image_index]
        if not Path(image_path).exists():
            QMessageBox.warning(self, "Ошибка", f"Файл не найден: {image_path}")
            self._clear_image()
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить изображение: {image_path}")
            self._clear_image()
            return

        self._base_pixmap = pixmap
        self._current_scale = 1.0
        self._offset = QPoint(0, 0)
        self._fit_to_view()
        self._update_image_counter()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._base_pixmap:
            self._fit_to_view()

    def _prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self._show_current_image()
            self._update_buttons_state()

    def _next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self._show_current_image()
            self._update_buttons_state()

    def _update_buttons_state(self):
        self.prev_btn.setEnabled(self.current_image_index > 0 and len(self.image_files) > 0)
        self.next_btn.setEnabled(self.current_image_index < len(self.image_files) - 1 and len(self.image_files) > 0)

    def _update_image_counter(self):
        total = len(self.image_files)
        current = self.current_image_index + 1 if total > 0 else 0
        self.image_counter.setText(f"{current}/{total}")

    def _clear_image(self):
        self.image_label.clear()
        self.image_counter.setText("0/0")

    def _clear_selection(self):
        self.folders_list.clearSelection()
        self.image_files = []
        self.current_image_index = 0
        self._update_buttons_state()
        self._clear_image()

    def _handle_subprojects_update(self):
        if self.current_project_index >= 0:
            self._project_selected(self.current_project_index)

    def _reload_projects(self):
        self._load_projects()

    def _fit_to_view(self):
        if not self._base_pixmap:
            return

        self._current_scale = 1.0
        self._offset = QPoint(0, 0)
        self._apply_zoom()

    def wheelEvent(self, event):
        if not self._base_pixmap:
            return

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            self._zoom_image(zoom_in)
        else:
            super().wheelEvent(event)

    def _zoom_image(self, zoom_in: bool):
        old_scale = self._current_scale
        self._current_scale = min(self._max_scale, max(self._min_scale,
                                                       self._current_scale + (
                                                           self._zoom_step if zoom_in else -self._zoom_step)))

        focus_point = self._get_focus_point()
        self._adjust_offset_after_zoom(old_scale, focus_point)
        self._apply_zoom()

    def _get_focus_point(self):
        pos = self.image_label.mapFromGlobal(self.cursor().pos())
        return QPoint(pos.x() - self._offset.x(), pos.y() - self._offset.y())

    def _adjust_offset_after_zoom(self, old_scale: float, focus_point: QPoint):
        scale_factor = self._current_scale / old_scale
        self._offset = QPoint(
            int((self._offset.x() + focus_point.x()) * scale_factor - focus_point.x()),
            int((self._offset.y() + focus_point.y()) * scale_factor - focus_point.y())
        )

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._base_pixmap:
            self._drag_start_pos = event.pos()
            self._is_dragging = True

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and self._base_pixmap:
            delta = event.pos() - self._drag_start_pos
            self._offset += delta
            self._drag_start_pos = event.pos()
            self._apply_zoom()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False

    def _apply_zoom(self):
        if not self._base_pixmap:
            return

        scaled_pixmap = self._base_pixmap.scaled(
            self._base_pixmap.size() * self._current_scale,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        pixmap_rect = scaled_pixmap.rect()
        label_rect = self.image_label.rect()

        x = max(min(self._offset.x(), pixmap_rect.width() - label_rect.width()), 0)
        y = max(min(self._offset.y(), pixmap_rect.height() - label_rect.height()), 0)

        self._offset = QPoint(x, y)
        cropped = scaled_pixmap.copy(x, y, label_rect.width(), label_rect.height())
        self.image_label.setPixmap(cropped)
