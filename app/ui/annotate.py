import os
import json
import shutil

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from app.utils.logger import log


IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']


class ClickableFrame(QFrame):
    clicked = Signal(str)

    def __init__(self, folder_name, parent=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.setStyleSheet("""
            QFrame {
                background: #F8F9FA;
                border-radius: 6px;
                border: 1px solid #DEE2E6;
                margin: 4px;
            }
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.folder_name)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background: #E9ECEF;
                border-radius: 6px;
                border: 1px solid #CED4DA;
                margin: 4px;
            }
        """)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background: #F8F9FA;
                border-radius: 6px;
                border: 1px solid #DEE2E6;
                margin: 4px;
            }
        """)


class QFlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._h_spacing = 10
        self._v_spacing = 10

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def setSpacing(self, spacing):
        self._h_spacing = spacing
        self._v_spacing = spacing

    def spacing(self):
        return self._h_spacing

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins().left() + self.contentsMargins().right()
        size += QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self._h_spacing

        for item in self._items:
            widget = item.widget()
            if widget is None:
                continue

            next_x = x + item.sizeHint().width() + spacing
            if next_x - spacing > rect.right() and line_height > 0:
                x = rect.x()
                y += line_height + self._v_spacing
                next_x = x + item.sizeHint().width() + spacing
                line_height = 0

            item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())


class AnnotatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.projects = []
        self.current_project = None
        self.current_subproject = None
        self.current_folder = None
        self.allocate_scroll_content = None
        self.image_layout = None
        self.stacked_widget = None
        self._initialize_ui()

    def _initialize_ui(self):
        self.stacked_widget = QStackedWidget()
        main_widget = self._create_main_widget()
        self.image_view_widget = self._create_image_view_widget()

        self.stacked_widget.addWidget(main_widget)
        self.stacked_widget.addWidget(self.image_view_widget)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.stacked_widget)

    def _create_main_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        dropdown_panel = self._create_dropdown_panel()
        layout.addWidget(dropdown_panel)

        top_section = QHBoxLayout()
        top_section.setSpacing(20)

        for title in ["Allocate", "Process", "Dataset"]:
            top_section.addWidget(self._create_panel(title))

        layout.addLayout(top_section)
        return widget

    def _create_dropdown_panel(self):
        container = QFrame()
        container.setObjectName("dropdownPanel")
        container.setStyleSheet("""
            QFrame#dropdownPanel {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        self.project_combo = QComboBox()
        self.project_combo.setPlaceholderText("Select Project")

        self.subproject_combo = QComboBox()
        self.subproject_combo.setPlaceholderText("Select Subproject")
        self.subproject_combo.currentIndexChanged.connect(self._on_subproject_selected)

        layout.addWidget(self.project_combo)
        layout.addWidget(self.subproject_combo)
        self.project_combo.currentIndexChanged.connect(self._on_project_selected)

        return container

    def _create_panel(self, title):
        container = QFrame()
        container.setObjectName("panelContainer")
        container.setStyleSheet("""
            QFrame#panelContainer {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        if title == "Allocate":
            self.btn_add = QPushButton("+")
            self.btn_add.setToolTip("Add images")
            self.btn_add.setStyleSheet(self._get_button_style("#4CAF50", "#3e8e41", "#43A047"))
            self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_add.clicked.connect(self._handle_add_images)
            header_layout.addWidget(self.btn_add)

        header.setLayout(header_layout)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(content_widget)

        layout.addWidget(scroll)
        container.setLayout(layout)

        if title == "Allocate":
            self.allocate_scroll_content = content_widget

        return container

    def _create_image_view_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        back_button = QPushButton("← Back")
        back_button.setStyleSheet(self._get_button_style("#6c757d", "#5a6268", "#545b62"))
        back_button.clicked.connect(self._return_to_main_view)
        layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignLeft)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        self.image_container = QWidget()
        self.image_layout = QFlowLayout(self.image_container)
        self.image_layout.setContentsMargins(5, 5, 5, 5)
        scroll.setWidget(self.image_container)

        layout.addWidget(scroll)
        return widget

    def showEvent(self, event):
        self._refresh_data()
        super().showEvent(event)

    def _refresh_data(self):
        self._load_projects()
        self.subproject_combo.clear()

    def _load_projects(self):
        self.projects = self._scan_projects()
        self.project_combo.clear()

        for project in self.projects:
            self.project_combo.addItem(project['name'], project)

    @staticmethod
    def _scan_projects() -> list[dict]:
        projects = []
        data_dir = "data"

        if not os.path.exists(data_dir):
            return projects

        for dir_name in os.listdir(data_dir):
            dir_path = os.path.join(data_dir, dir_name)
            meta_path = os.path.join(dir_path, "meta.json")

            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        if meta.get('type') == 'project':
                            project_data = {
                                'name': meta.get('name', dir_name),
                                'path': dir_path,
                                'subprojects': meta.get('subprojects', [])
                            }
                            projects.append(project_data)
                except Exception as e:
                    log("ERROR", f"Error reading {meta_path}: {str(e)}")
        return projects

    def _on_project_selected(self, index):
        if index == -1:
            return

        project = self.project_combo.itemData(index)
        self.current_project = project
        self._load_subprojects(project)

    def _load_subprojects(self, project):
        subprojects = self._scan_subprojects(project)
        self.subproject_combo.clear()

        if not subprojects:
            self.subproject_combo.setPlaceholderText("No subprojects available")
            self.subproject_combo.setEnabled(False)
            return

        for subproject in subprojects:
            self.subproject_combo.addItem(subproject['name'], subproject)

        self.subproject_combo.setPlaceholderText("Select subproject")
        self.subproject_combo.setEnabled(True)
        self.subproject_combo.setCurrentIndex(-1)

    @staticmethod
    def _scan_subprojects(project: dict) -> list[dict]:
        subprojects = []
        meta_path = os.path.join(project['path'], "meta.json")

        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                project_meta = json.load(f)
                for sp_name in project_meta.get('subprojects', []):
                    sp_path = os.path.join(project['path'], 'subprojects', sp_name)
                    if os.path.exists(sp_path):
                        subprojects.append({'name': sp_name, 'path': sp_path})
        except Exception as e:
            log("ERROR", f"Error reading {meta_path}: {str(e)}")

        return subprojects

    def _on_subproject_selected(self, index):
        if index == -1:
            return

        subproject = self.subproject_combo.itemData(index)
        self.current_subproject = subproject
        self._update_allocate_blocks()

    def _handle_add_images(self):
        if not self.current_subproject:
            QMessageBox.warning(self, "Error", "Please select subproject first!")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select image folder")
        if not folder:
            return

        valid_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    valid_files.append(os.path.join(root, file))

        if not valid_files:
            QMessageBox.warning(self, "Error", "No valid image files found!")
            return

        target_dir = os.path.join(self.current_subproject['path'], 'images')
        os.makedirs(target_dir, exist_ok=True)

        base_name = os.path.basename(folder)
        dest_folder = os.path.join(target_dir, base_name)
        counter = 1
        while os.path.exists(dest_folder):
            dest_folder = f"{os.path.join(target_dir, base_name)}_{counter}"
            counter += 1
        os.makedirs(dest_folder)

        for file in valid_files:
            shutil.copy2(file, dest_folder)

        self._update_allocate_blocks()
        QMessageBox.information(self, "Success", f"Added {len(valid_files)} images!")

    def _update_allocate_blocks(self):
        if self.allocate_scroll_content.layout():
            while self.allocate_scroll_content.layout().count():
                item = self.allocate_scroll_content.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        if not self.current_subproject:
            return

        image_dir = os.path.join(self.current_subproject['path'], 'images')
        if not os.path.exists(image_dir):
            return

        for folder in os.listdir(image_dir):
            folder_path = os.path.join(image_dir, folder)
            if os.path.isdir(folder_path):
                count = len([f for f in os.listdir(folder_path)
                             if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS])

                block = ClickableFrame(folder)
                block.setToolTip(f"Double click to open {folder}")

                layout = QHBoxLayout(block)
                layout.addWidget(QLabel(folder))
                layout.addStretch()
                layout.addWidget(QLabel(f"{count} images"))

                block.clicked.connect(self._handle_folder_click)

                self.allocate_scroll_content.layout().addWidget(block)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            obj.setStyleSheet("""
                QFrame {
                    background: #E9ECEF;
                    border-radius: 6px;
                    border: 1px solid #CED4DA;
                    margin: 4px;
                }
            """)
        elif event.type() == QEvent.Type.Leave:
            obj.setStyleSheet("""
                QFrame {
                    background: #F8F9FA;
                    border-radius: 6px;
                    border: 1px solid #DEE2E6;
                    margin: 4px;
                }
            """)
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        if child and isinstance(child.parent(), QFrame):
            folder = child.parent().findChild(QLabel).text().split('\n')[0]
            self._handle_folder_click(folder)

    def _handle_folder_click(self, folder_name):
        log("CLICK", f"Folder clicked: {folder_name}")
        reply = QMessageBox.question(
            self,
            "Confirm Open",
            f"Open folder '{folder_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_folder = folder_name
            self._show_image_view()

    def _show_image_view(self):
        self._populate_image_view()
        self.stacked_widget.setCurrentIndex(1)

    def _populate_image_view(self):
        while self.image_layout.count():
            item = self.image_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        folder_path = os.path.join(
            self.current_subproject['path'],
            'images',
            self.current_folder
        )

        for file in sorted(os.listdir(folder_path)):
            if os.path.splitext(file)[1].lower() in IMAGE_EXTENSIONS:
                try:
                    pixmap = QPixmap(os.path.join(folder_path, file))
                    label = QLabel()
                    label.setPixmap(pixmap.scaled(200, 200,
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation))
                    label.setStyleSheet("""
                        QLabel {
                            border-radius: 8px;
                            border: 2px solid #dee2e6;
                            margin: 5px;
                            background-color: #ffffff;
                        }
                    """)
                    self.image_layout.addWidget(label)
                except Exception as e:
                    log("ERROR", f"Error loading image {file}: {str(e)}")

    def _return_to_main_view(self):
        self.stacked_widget.setCurrentIndex(0)

    @staticmethod
    def _get_button_style(normal: str, hover: str, pressed: str) -> str:
        return f"""
            QPushButton {{
                background-color: {normal};
                color: white;
                border-radius: 6px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                font-weight: bold;
                border: none;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """
