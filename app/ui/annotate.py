import os
import json
import shutil
import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *


def log(category, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"[{timestamp}] [{category}] {message}")
    print("-" * 150)


IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']


class AnnotatePage(QWidget):
    def __init__(self):
        super().__init__()
        log("INIT", "Initializing AnnotatePage")
        self.projects = []
        self.current_project = None
        self.current_subproject = None
        self.allocate_scroll_content = None
        self.setup_ui()

    def setup_ui(self):
        log("UI", "Starting UI setup")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.setStyleSheet("AnnotatePage {background-color: #f0f0f0;}")
        log("UI", "Main page style applied")

        dropdown_panel = self._create_dropdown_panel()
        main_layout.addWidget(dropdown_panel)
        log("UI", "Dropdown panel added")

        top_section = QHBoxLayout()
        top_section.setSpacing(20)

        for title in ["Allocate", "Process", "Dataset"]:
            log("UI", f"Creating panel: {title}")
            top_section.addWidget(self._create_panel(title))
            log("UI", f"Panel {title} added to layout")

        main_layout.addLayout(top_section)
        main_layout.setStretch(1, 1)
        self.setLayout(main_layout)
        log("UI", "Main layout setup completed")

    def _create_dropdown_panel(self):
        log("UI", "Creating project selection panel")
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
        log("UI", "Dropdown panel styles applied")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        self.project_combo = QComboBox()
        self.project_combo.setPlaceholderText("Select Project")
        log("UI", "Project combobox created")

        self.subproject_combo = QComboBox()
        self.subproject_combo.setPlaceholderText("Select Subproject")
        self.subproject_combo.currentIndexChanged.connect(self._on_subproject_selected)
        log("UI", "Subproject combobox created with signal connection")

        layout.addWidget(self.project_combo)
        layout.addWidget(self.subproject_combo)
        self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        log("UI", "Dropdown elements added to layout")

        return container

    def showEvent(self, event):
        log("EVENT", "Page display event triggered")
        self._refresh_data()
        super().showEvent(event)
        log("EVENT", "Page display handling completed")

    def _refresh_data(self):
        log("DATA", "Starting data refresh")
        self._load_projects()
        self.subproject_combo.clear()
        log("DATA", "Subproject list cleared")

    def _load_projects(self):
        log("DATA", "Loading projects from filesystem")
        self.projects = self._scan_projects()
        self.project_combo.clear()
        log("DATA", "Project combobox cleared")

        for index, project in enumerate(self.projects):
            self.project_combo.addItem(project['name'], project)
            log("DATA", f"Added project [{index}]: {project['name']}")

    def _scan_projects(self):
        log("FS", "Scanning data directory")
        projects = []
        data_dir = "data"

        if not os.path.exists(data_dir):
            log("ERROR", "Data directory not found!")
            return projects

        for dir_name in os.listdir(data_dir):
            dir_path = os.path.join(data_dir, dir_name)
            meta_path = os.path.join(dir_path, "meta.json")
            log("FS", f"Checking path: {dir_path}")

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
                            log("PROJECT", f"Found project: {project_data['name']}")
                except Exception as e:
                    log("ERROR", f"Error reading {meta_path}: {str(e)}")
        return projects

    def _on_project_selected(self, index):
        log("EVENT", f"Project selected with index: {index}")
        if index == -1:
            log("EVENT", "Project selection reset")
            return

        project = self.project_combo.itemData(index)
        self.current_project = project
        log("SELECTION", f"Selected project: {project['name']}")
        self._load_subprojects(project)

    def _load_subprojects(self, project):
        log("DATA", f"Loading subprojects for {project['name']}")
        subprojects = self._scan_subprojects(project)
        self.subproject_combo.clear()
        log("UI", "Subproject combobox cleared")

        if not subprojects:
            log("WARNING", "No subprojects found")
            self.subproject_combo.setPlaceholderText("No subprojects available")
            self.subproject_combo.setEnabled(False)
            return

        for idx, subproject in enumerate(subprojects):
            self.subproject_combo.addItem(subproject['name'], subproject)
            log("DATA", f"Added subproject [{idx}]: {subproject['name']}")

        self.subproject_combo.setPlaceholderText("Select subproject")
        self.subproject_combo.setEnabled(True)
        self.subproject_combo.setCurrentIndex(-1)
        log("UI", "Subproject combobox configured")

    def _scan_subprojects(self, project):
        log("FS", f"Scanning subprojects in {project['path']}")
        subprojects = []
        meta_path = os.path.join(project['path'], "meta.json")

        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                project_meta = json.load(f)
                log("META", f"Read meta.json for project {project['name']}")

                for sp_name in project_meta.get('subprojects', []):
                    sp_path = os.path.join(project['path'], 'subprojects', sp_name)
                    if os.path.exists(sp_path):
                        subprojects.append({'name': sp_name, 'path': sp_path})
                        log("SUBPROJECT", f"Found subproject: {sp_name}")
                    else:
                        log("ERROR", f"Subproject folder not found: {sp_path}")
        except Exception as e:
            log("ERROR", f"Error reading {meta_path}: {str(e)}")

        return subprojects

    def _on_subproject_selected(self, index):
        log("EVENT", f"Subproject selected with index: {index}")
        if index == -1:
            log("EVENT", "Subproject selection reset")
            return

        subproject = self.subproject_combo.itemData(index)
        self.current_subproject = subproject
        log("SELECTION", f"Selected subproject: {subproject['name']}")
        self._update_allocate_blocks()

    def _create_panel(self, title):
        log("UI", f"Creating panel: {title}")
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

    def _handle_add_images(self):
        log("ACTION", "Starting image addition process")
        if not self.current_subproject:
            QMessageBox.warning(self, "Error", "Please select subproject first!")
            log("ERROR", "Attempted to add images without subproject selection")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select image folder")
        if not folder:
            log("ACTION", "User canceled folder selection")
            return

        log("FS", f"Selected folder: {folder}")
        valid_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    valid_files.append(os.path.join(root, file))
        log("FS", f"Found {len(valid_files)} valid files")

        if not valid_files:
            QMessageBox.warning(self, "Error", "No valid image files found!")
            log("ERROR", "No valid images in selected folder")
            return

        target_dir = os.path.join(self.current_subproject['path'], 'images')
        os.makedirs(target_dir, exist_ok=True)
        log("FS", f"Created target directory: {target_dir}")

        base_name = os.path.basename(folder)
        dest_folder = os.path.join(target_dir, base_name)
        counter = 1
        while os.path.exists(dest_folder):
            dest_folder = f"{os.path.join(target_dir, base_name)}_{counter}"
            counter += 1
        os.makedirs(dest_folder)
        log("FS", f"Created unique folder: {dest_folder}")

        for file in valid_files:
            shutil.copy(file, dest_folder)
            log("COPY", f"Copied file: {file} -> {dest_folder}")

        self._update_allocate_blocks()
        QMessageBox.information(self, "Success", f"Added {len(valid_files)} images!")
        log("ACTION", "Image addition process completed")

    def _update_allocate_blocks(self):
        log("UI", "Updating image blocks")
        if self.allocate_scroll_content.layout():
            while self.allocate_scroll_content.layout().count():
                item = self.allocate_scroll_content.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            log("UI", "Old blocks removed")

        if not self.current_subproject:
            log("WARNING", "No subproject selected for update")
            return

        image_dir = os.path.join(self.current_subproject['path'], 'images')
        if not os.path.exists(image_dir):
            log("WARNING", "Image directory not found")
            return

        for folder in os.listdir(image_dir):
            folder_path = os.path.join(image_dir, folder)
            if os.path.isdir(folder_path):
                count = len([f for f in os.listdir(folder_path)
                             if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS])

                block = QFrame()
                block.setStyleSheet("""
                    QFrame {
                        background: #F8F9FA;
                        border-radius: 6px;
                        border: 1px solid #DEE2E6;
                        margin: 4px;
                    }
                """)

                layout = QHBoxLayout(block)
                layout.addWidget(QLabel(folder))
                layout.addStretch()
                layout.addWidget(QLabel(f"{count} images"))

                self.allocate_scroll_content.layout().addWidget(block)
                log("UI", f"Added block: {folder} ({count} images)")

    def _get_button_style(self, normal, hover, pressed):
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
