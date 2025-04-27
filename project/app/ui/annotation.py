import json
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QPushButton, QFrame,
                             QMessageBox, QDialog, QDialogButtonBox, QInputDialog)
from PyQt6.QtGui import (QPixmap, QMouseEvent, QPainter, QPen, QColor, QPolygon, QCursor)


class AnnotationTab(QWidget):
    """Вкладка для разметки изображений с поддержкой прямоугольников, полигонов и точек"""

    def __init__(self, projects_tab=None, subprojects_tab=None, distribution_tab=None):
        super().__init__()
        self.projects = []
        self.current_project_index = -1
        self.current_project_data = None
        self.current_subproject_index = -1
        self.current_image_index = 0
        self.image_files = []

        # Состояние разметки
        self.current_tool = None
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_rect = None
        self.current_polygon = []
        self.current_point = None
        self.annotations = []
        self.selected_class = None
        self.selected_annotation_index = -1
        self.dragging_handle = -1
        self.hovered_handle = -1

        # Масштабирование и перемещение
        self._current_scale = 1.0
        self._base_pixmap = None
        self._min_scale = 0.1
        self._max_scale = 3.0
        self._zoom_step = 0.1
        self._offset = QPoint(0, 0)
        self._drag_start_pos = QPoint()
        self._is_dragging = False
        self._is_panning = False

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

        # Левая панель - выбор проекта и папок
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        project_panel = QFrame()
        project_panel.setFrameShape(QFrame.Shape.StyledPanel)
        project_panel.setStyleSheet("background-color: #2D2D2D;")
        project_layout = QVBoxLayout(project_panel)

        # Выбор проекта
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

        # Выбор подпроекта
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

        # Список папок
        self.folders_list = QListWidget()
        self.folders_list.setStyleSheet("""
            QListWidget {
                background-color: #3D3D3D;
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
        self.folders_list.itemClicked.connect(self._folder_selected)
        left_layout.addWidget(self.folders_list)

        main_layout.addWidget(left_panel)

        # Центральная панель - изображение
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)

        # Панель навигации
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

        # Метка для изображения
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

        # Правая панель - инструменты
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

        # Кнопки инструментов
        self.rect_tool = QPushButton("Прямоугольник")
        self.rect_tool.setStyleSheet(self.prev_btn.styleSheet())
        self.rect_tool.clicked.connect(self._activate_rect_tool)
        right_layout.addWidget(self.rect_tool)

        self.polygon_tool = QPushButton("Полигон")
        self.polygon_tool.setStyleSheet(self.prev_btn.styleSheet())
        self.polygon_tool.clicked.connect(self._activate_polygon_tool)
        right_layout.addWidget(self.polygon_tool)

        self.point_tool = QPushButton("Точка")
        self.point_tool.setStyleSheet(self.prev_btn.styleSheet())
        self.point_tool.clicked.connect(self._activate_point_tool)
        right_layout.addWidget(self.point_tool)

        # Кнопка сохранения
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
        self.save_btn.clicked.connect(self._save_annotations)
        right_layout.addWidget(self.save_btn)

        right_layout.addStretch()
        main_layout.addWidget(right_panel)

        self.setLayout(main_layout)
        self._update_buttons_state()

    # Методы для работы с проектами и изображениями
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

    # Методы для масштабирования и перемещения изображения
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

    # Методы для работы с инструментами разметки
    def _activate_rect_tool(self):
        """Активирует инструмент прямоугольника"""
        self.current_tool = "rect"
        self._show_class_selection_dialog()

    def _activate_polygon_tool(self):
        """Активирует инструмент полигона"""
        self.current_tool = "polygon"
        self._show_class_selection_dialog()

    def _activate_point_tool(self):
        """Активирует инструмент точки"""
        self.current_tool = "point"
        self._show_class_selection_dialog()

    def _show_class_selection_dialog(self):
        """Показывает диалог выбора класса для аннотации"""
        if not self.current_project_data or self.current_subproject_index == -1:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите подпроект")
            self.current_tool = None
            return

        subproject = self.current_project_data["subprojects"][self.current_subproject_index]
        classes = subproject.get("classes", [])

        if not classes:
            QMessageBox.warning(self, "Ошибка", "В этом подпроекте нет классов для разметки")
            self.current_tool = None
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите класс")
        dialog.setFixedSize(300, 200)

        layout = QVBoxLayout()

        class_list = QListWidget()
        for cls in classes:
            item = QListWidgetItem(cls["name"])
            item.setData(Qt.ItemDataRole.UserRole, cls)
            item.setBackground(QColor(cls["color"]))
            item.setForeground(QColor("black") if QColor(cls["color"]).lightness() > 127 else QColor("white"))
            class_list.addItem(item)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(QLabel("Выберите класс для разметки:"))
        layout.addWidget(class_list)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_item = class_list.currentItem()
            if selected_item:
                self.selected_class = selected_item.data(Qt.ItemDataRole.UserRole)
                # Изменяем курсор при выборе инструмента
                if self.current_tool == "rect":
                    self.setCursor(Qt.CursorShape.CrossCursor)
                elif self.current_tool == "polygon":
                    self.setCursor(Qt.CursorShape.CrossCursor)
                elif self.current_tool == "point":
                    self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.current_tool = None
            self.selected_class = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _map_to_image(self, pos: QPoint) -> QPoint:
        """Преобразует координаты виджета в координаты изображения с учетом масштаба и смещения"""
        if not self._base_pixmap:
            return QPoint()

        label_pos = self.image_label.mapFromParent(pos)
        x = int((label_pos.x() - self._offset.x()) / self._current_scale)
        y = int((label_pos.y() - self._offset.y()) / self._current_scale)

        return QPoint(x, y)

    def _map_from_image(self, pos: QPoint) -> QPoint:
        """Преобразует координаты изображения в координаты виджета с учетом масштаба и смещения"""
        if not self._base_pixmap:
            return QPoint()

        x = int(pos.x() * self._current_scale + self._offset.x())
        y = int(pos.y() * self._current_scale + self._offset.y())

        return QPoint(x, y)

    def _get_handle_rect(self, pos: QPoint) -> QRect:
        """Возвращает прямоугольник для ручки изменения размера"""
        handle_size = 8
        return QRect(pos.x() - handle_size // 2, pos.y() - handle_size // 2, handle_size, handle_size)

    def mousePressEvent(self, event: QMouseEvent):
        if not self._base_pixmap:
            return

        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = True
            self._drag_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        # Преобразуем координаты относительно image_label
        label_pos = self.image_label.mapFromParent(event.pos())
        if not self.image_label.rect().contains(label_pos):
            return

        if event.button() == Qt.MouseButton.LeftButton:
            pos = self._map_to_image(label_pos)  # Используем преобразованные координаты

            # Проверяем, не попали ли мы в ручку изменения размера
            if self.selected_annotation_index >= 0:
                annotation = self.annotations[self.selected_annotation_index]
                if annotation["type"] == "rect":
                    rect = QRect(*annotation["coordinates"])
                    corners = [
                        rect.topLeft(), rect.topRight(),
                        rect.bottomRight(), rect.bottomLeft()
                    ]
                    for i, corner in enumerate(corners):
                        handle_pos = self._map_from_image(corner)
                        if self._get_handle_rect(handle_pos).contains(label_pos):
                            self.dragging_handle = i
                            return

            if self.current_tool == "rect" and self.selected_class:
                self.drawing = True
                self.start_point = pos
                self.end_point = pos
                self.update()
            elif self.current_tool == "polygon" and self.selected_class:
                self.current_polygon.append(pos)
                self.update()
            elif self.current_tool == "point" and self.selected_class:
                self.current_point = pos
                self._add_annotation()
                self.update()
            else:
                # Проверяем, не выбрали ли мы существующую аннотацию
                for i, ann in enumerate(self.annotations):
                    if ann["image"] != self.image_files[self.current_image_index]:
                        continue

                    if ann["type"] == "rect":
                        x, y, w, h = ann["coordinates"]
                        rect = QRect(x, y, w, h)
                        if rect.contains(pos):
                            self.selected_annotation_index = i
                            self.dragging_handle = -1
                            self.drag_start_pos = pos
                            break
                    elif ann["type"] == "polygon":
                        polygon = QPolygon([QPoint(x, y) for x, y in ann["coordinates"]])
                        if polygon.containsPoint(pos, Qt.FillRule.OddEvenFill):
                            self.selected_annotation_index = i
                            self.drag_start_pos = pos
                            break
                    elif ann["type"] == "point":
                        x, y = ann["coordinates"]
                        point_rect = QRect(x - 5, y - 5, 10, 10)
                        if point_rect.contains(pos):
                            self.selected_annotation_index = i
                            self.drag_start_pos = pos
                            break

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._base_pixmap:
            return

        if self._is_panning:
            delta = event.pos() - self._drag_start_pos
            self._offset += delta
            self._drag_start_pos = event.pos()
            self._apply_zoom()
            return

        # Преобразуем координаты относительно image_label
        label_pos = self.image_label.mapFromParent(event.pos())
        if not self.image_label.rect().contains(label_pos):
            return

        pos = self._map_to_image(label_pos)

        # Обновляем курсор при наведении на ручки изменения размера
        if self.selected_annotation_index >= 0:
            annotation = self.annotations[self.selected_annotation_index]
            if annotation["type"] == "rect":
                rect = QRect(*annotation["coordinates"])
                corners = [
                    rect.topLeft(), rect.topRight(),
                    rect.bottomRight(), rect.bottomLeft()
                ]
                for i, corner in enumerate(corners):
                    handle_pos = self._map_from_image(corner)
                    if self._get_handle_rect(handle_pos).contains(label_pos):
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor if i % 2 == 0 else Qt.CursorShape.SizeBDiagCursor)
                        self.hovered_handle = i
                        break
                else:
                    self.hovered_handle = -1
                    if self.current_tool == "rect":
                        self.setCursor(Qt.CursorShape.CrossCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.hovered_handle = -1

        # Перемещение аннотации
        if self.selected_annotation_index >= 0 and not self.drawing:
            if self.dragging_handle >= 0:
                # Изменение размера через ручку
                annotation = self.annotations[self.selected_annotation_index]
                if annotation["type"] == "rect":
                    x, y, w, h = annotation["coordinates"]
                    rect = QRect(x, y, w, h)

                    if self.dragging_handle == 0:  # top-left
                        rect.setTopLeft(pos)
                    elif self.dragging_handle == 1:  # top-right
                        rect.setTopRight(pos)
                    elif self.dragging_handle == 2:  # bottom-right
                        rect.setBottomRight(pos)
                    elif self.dragging_handle == 3:  # bottom-left
                        rect.setBottomLeft(pos)

                    annotation["coordinates"] = [rect.x(), rect.y(), rect.width(), rect.height()]
            else:
                # Перемещение всей аннотации
                delta = pos - self.drag_start_pos
                annotation = self.annotations[self.selected_annotation_index]

                if annotation["type"] == "rect":
                    x, y, w, h = annotation["coordinates"]
                    annotation["coordinates"] = [x + delta.x(), y + delta.y(), w, h]
                elif annotation["type"] == "polygon":
                    annotation["coordinates"] = [[p.x() + delta.x(), p.y() + delta.y()] for p in
                                                 [QPoint(x, y) for x, y in annotation["coordinates"]]]
                elif annotation["type"] == "point":
                    x, y = annotation["coordinates"]
                    annotation["coordinates"] = [x + delta.x(), y + delta.y()]

                self.drag_start_pos = pos

            self.update()
        elif self.drawing and self.current_tool == "rect" and self.selected_class:
            self.end_point = pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor if not self.current_tool else Qt.CursorShape.CrossCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.drawing and self.current_tool == "rect":
                self.drawing = False
                self.end_point = self._map_to_image(event.pos())
                self._add_annotation()
                self.update()

            self.dragging_handle = -1

    def _add_annotation(self):
        """Добавляет аннотацию в список"""
        if self.current_tool == "rect":
            rect = QRect(self.start_point, self.end_point).normalized()
            if rect.width() < 5 or rect.height() < 5:  # Минимальный размер
                return

            self.annotations.append({
                "type": "rect",
                "class": self.selected_class["name"],
                "color": self.selected_class["color"],
                "coordinates": [rect.x(), rect.y(), rect.width(), rect.height()],
                "image": self.image_files[self.current_image_index]
            })
        elif self.current_tool == "polygon":
            if len(self.current_polygon) > 2:
                self.annotations.append({
                    "type": "polygon",
                    "class": self.selected_class["name"],
                    "color": self.selected_class["color"],
                    "coordinates": [[p.x(), p.y()] for p in self.current_polygon],
                    "image": self.image_files[self.current_image_index]
                })
        elif self.current_tool == "point":
            self.annotations.append({
                "type": "point",
                "class": self.selected_class["name"],
                "color": self.selected_class["color"],
                "coordinates": [self.current_point.x(), self.current_point.y()],
                "image": self.image_files[self.current_image_index]
            })

        # Сбрасываем состояние рисования
        self._reset_annotation_state()

    def _reset_annotation_state(self):
        """Сбрасывает состояние аннотации"""
        self.current_tool = None
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_rect = None
        self.current_polygon = []
        self.current_point = None
        self.selected_class = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _save_annotations(self):
        """Сохраняет все аннотации в файлы"""
        if not self.annotations:
            QMessageBox.warning(self, "Ошибка", "Нет аннотаций для сохранения")
            return

        # Определяем путь для сохранения аннотаций
        project_name = self.projects[self.current_project_index]["name"]
        subproject_name = self.current_project_data["subprojects"][self.current_subproject_index]["name"]
        annotations_dir = Path(__file__).parent.parent.parent / "data" / "annotations" / project_name / subproject_name
        annotations_dir.mkdir(parents=True, exist_ok=True)

        # Группируем аннотации по изображениям
        image_annotations = {}
        for ann in self.annotations:
            if ann["image"] not in image_annotations:
                image_annotations[ann["image"]] = []
            image_annotations[ann["image"]].append(ann)

        # Сохраняем аннотации для каждого изображения
        for image_path, annotations in image_annotations.items():
            image_name = Path(image_path).stem
            annotation_file = annotations_dir / f"{image_name}.json"

            with open(annotation_file, 'w', encoding='utf-8') as f:
                json.dump(annotations, f, indent=2, ensure_ascii=False)

        QMessageBox.information(self, "Сохранено", "Аннотации успешно сохранены")
        self.annotations = []
        self.selected_annotation_index = -1

    def paintEvent(self, event):
        """Отрисовывает аннотации на изображении"""
        super().paintEvent(event)

        if not self._base_pixmap:
            return

        painter = QPainter(self.image_label)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Рисуем текущую аннотацию в процессе создания (прямоугольник)
        if self.selected_class and self.current_tool == "rect" and self.start_point and self.end_point:
            # Настройки пера для текущего прямоугольника
            pen = QPen(QColor(self.selected_class["color"]), 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # Прозрачная заливка

            # Преобразуем координаты для отображения
            start_x = int(self.start_point.x() * self._current_scale + self._offset.x())
            start_y = int(self.start_point.y() * self._current_scale + self._offset.y())
            end_x = int(self.end_point.x() * self._current_scale + self._offset.x())
            end_y = int(self.end_point.y() * self._current_scale + self._offset.y())

            # Рисуем прямоугольник
            rect = QRect(QPoint(start_x, start_y), QPoint(end_x, end_y)).normalized()
            painter.drawRect(rect)

            # Рисуем текст с именем класса
            painter.setPen(QPen(QColor("white"), 1))
            painter.drawText(rect.topLeft() + QPoint(5, 15), self.selected_class["name"])

        # Рисуем существующие аннотации для текущего изображения
        for i, ann in enumerate(self.annotations):
            if ann["image"] != self.image_files[self.current_image_index]:
                continue

            # Настройки пера для существующих аннотаций
            pen = QPen(QColor(ann["color"]), 3 if i == self.selected_annotation_index else 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # Прозрачная заливка

            if ann["type"] == "rect":
                x, y, w, h = ann["coordinates"]
                rect = QRect(
                    int(x * self._current_scale + self._offset.x()),
                    int(y * self._current_scale + self._offset.y()),
                    int(w * self._current_scale),
                    int(h * self._current_scale)
                )
                painter.drawRect(rect)

                # Рисуем текст с именем класса
                painter.setPen(QPen(QColor("white"), 1))
                painter.drawText(rect.topLeft() + QPoint(5, 15), ann["class"])

                # Рисуем ручки изменения размера для выбранного прямоугольника
                if i == self.selected_annotation_index:
                    painter.setPen(QPen(QColor("white"), 1))
                    painter.setBrush(QColor(ann["color"]))

                    corners = [
                        rect.topLeft(), rect.topRight(),
                        rect.bottomRight(), rect.bottomLeft()
                    ]

                    for corner in corners:
                        handle_rect = self._get_handle_rect(corner)
                        painter.drawRect(handle_rect)

            elif ann["type"] == "polygon":
                polygon = QPolygon()
                for x, y in ann["coordinates"]:
                    polygon.append(QPoint(
                        int(x * self._current_scale + self._offset.x()),
                        int(y * self._current_scale + self._offset.y())
                    ))
                painter.drawPolygon(polygon)

                # Рисуем текст с именем класса
                if polygon.size() > 0:
                    painter.setPen(QPen(QColor("white"), 1))
                    painter.drawText(polygon.boundingRect().topLeft() + QPoint(5, 15), ann["class"])

            elif ann["type"] == "point":
                x, y = ann["coordinates"]
                center = QPoint(
                    int(x * self._current_scale + self._offset.x()),
                    int(y * self._current_scale + self._offset.y())
                )
                painter.drawEllipse(center, 5, 5)

                # Рисуем текст с именем класса
                painter.setPen(QPen(QColor("white"), 1))
                painter.drawText(center + QPoint(8, 5), ann["class"])

        painter.end()
