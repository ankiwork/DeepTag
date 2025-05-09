import os
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from app.utils.logger import log


class AnnotatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.projects = []
        self.current_project = None
        self.current_subproject = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        log("UI", "Initializing main layout")
        self.setStyleSheet("AnnotatePage {background-color: #f0f0f0;}")

        dropdown_panel = self._create_dropdown_panel()
        main_layout.addWidget(dropdown_panel)

        top_section = QHBoxLayout()
        top_section.setSpacing(20)

        for title in ["Allocate", "Process", "Dataset"]:
            log("UI", f"Creating panel: {title}")
            top_section.addWidget(self._create_panel(title))

        main_layout.addLayout(top_section)
        main_layout.setStretch(1, 1)
        self.setLayout(main_layout)
        log("UI", "Main layout setup completed")

    def _create_dropdown_panel(self):
        log("UI", "Creating dropdown panel")
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
        log("UI", "Created project combo box")
        layout.addWidget(self.project_combo)

        self.subproject_combo = QComboBox()
        self.subproject_combo.setPlaceholderText("Select Subproject")
        self.subproject_combo.currentIndexChanged.connect(self._on_subproject_selected)
        log("UI", "Created subproject combo box")
        layout.addWidget(self.subproject_combo)

        self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        return container

    def showEvent(self, event):
        log("EVENT", "Page show event triggered")
        super().showEvent(event)
        self._refresh_data()

    def _refresh_data(self):
        log("DATA", "Starting data refresh process")
        self._load_projects()
        self.subproject_combo.clear()
        log("UI", "Cleared subproject combo box")

    def _load_projects(self):
        log("DATA", "Loading projects from filesystem")
        self.projects = self._scan_projects()
        self.project_combo.clear()
        log("UI", "Cleared project combo box")

        log("DATA", f"Found {len(self.projects)} total projects")
        for index, project in enumerate(self.projects):
            self.project_combo.addItem(project['name'], project)
            log("DATA", f"Added project [{index}]: {project['name']} "
                              f"(Path: {os.path.abspath(project['path'])})")

    def _scan_projects(self):
        projects = []
        data_dir = "data"
        log("FS", f"Scanning directory: {os.path.abspath(data_dir)}")

        if not os.path.exists(data_dir):
            log("ERROR", f"Data directory not found: {os.path.abspath(data_dir)}")
            return projects

        for dir_name in os.listdir(data_dir):
            dir_path = os.path.join(data_dir, dir_name)
            meta_path = os.path.join(dir_path, "meta.json")
            log("FS", f"Checking path: {os.path.abspath(dir_path)}")

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
                            log("PROJECT",
                                      f"Found valid project: {project_data['name']}\n"
                                      f"  Path: {os.path.abspath(dir_path)}\n"
                                      f"  Meta: {meta_path}\n"
                                      f"  Subprojects: {meta.get('subprojects', [])}")
                except Exception as e:
                    log("ERROR", f"Failed to read {meta_path}: {str(e)}")
        return projects

    def _on_project_selected(self, index):
        if index == -1:
            log("EVENT", "Project selection reset to -1")
            return

        project = self.project_combo.itemData(index)
        self.current_project = project
        log("SELECTION",
                  f"Project selected:\n"
                  f"  Name: {project['name']}\n"
                  f"  Path: {os.path.abspath(project['path'])}\n"
                  f"  Index: {index}")
        self._load_subprojects(project)

    def _load_subprojects(self, project):
        log("DATA", f"Loading subprojects for: {project['name']}")
        subprojects = self._scan_subprojects(project)
        self.subproject_combo.clear()
        log("UI", "Cleared subproject combo box")

        if not subprojects:
            log("DATA", f"No subprojects found for {project['name']}")
            self.subproject_combo.setPlaceholderText("No subprojects available")
            self.subproject_combo.setEnabled(False)
            return

        log("DATA", f"Found {len(subprojects)} subprojects in {project['name']}")
        for idx, subproject in enumerate(subprojects):
            self.subproject_combo.addItem(subproject['name'], subproject)
            log("DATA", f"Added subproject [{idx}]: {subproject['name']} "
                              f"(Path: {os.path.abspath(subproject['path'])})")

        self.subproject_combo.setPlaceholderText("Select subproject")
        self.subproject_combo.setEnabled(True)
        self.subproject_combo.setCurrentIndex(-1)
        log("UI", "Subproject combo box updated")

    def _scan_subprojects(self, project):
        subprojects = []
        meta_path = os.path.join(project['path'], "meta.json")
        log("FS", f"Scanning subprojects in: {os.path.abspath(project['path'])}")

        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                project_meta = json.load(f)
                log("META",
                          f"Reading project meta:\n"
                          f"  Path: {os.path.abspath(meta_path)}\n"
                          f"  Subprojects: {project_meta.get('subprojects', [])}")

                for sp_name in project_meta.get('subprojects', []):
                    sp_path = os.path.join(project['path'], sp_name)
                    subproject = {'name': sp_name, 'path': sp_path}
                    subprojects.append(subproject)
                    log("SUBPROJECT",
                              f"Found subproject entry:\n"
                              f"  Name: {sp_name}\n"
                              f"  Path: {os.path.abspath(sp_path)}")

        except Exception as e:
            log("ERROR", f"Failed to read {meta_path}: {str(e)}")

        return subprojects

    def _on_subproject_selected(self, index):
        if index == -1:
            log("EVENT", "Subproject selection reset to -1")
            return

        subproject = self.subproject_combo.itemData(index)
        self.current_subproject = subproject
        log("SELECTION",
                  f"Subproject selected:\n"
                  f"  Name: {subproject['name']}\n"
                  f"  Path: {os.path.abspath(subproject['path'])}\n"
                  f"  Index: {index}")

    @staticmethod
    def _create_panel(title):
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
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
                background-color: #ffffff;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)

        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)

        layout.addWidget(title_label)
        layout.addWidget(content)
        layout.setStretch(1, 1)
        container.setLayout(layout)
        return container
