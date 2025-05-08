import os
import json
import re
from datetime import datetime
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                               QPushButton, QSpacerItem, QSizePolicy, QScrollArea,
                               QDialog, QLineEdit, QMessageBox, QListWidget,
                               QListWidgetItem, QAbstractItemView)


class ConfirmationDialog(QDialog):
    def __init__(self, project_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Deletion")
        self.setFixedSize(350, 150)

        layout = QVBoxLayout()
        self.label = QLabel(f"Type project name to confirm deletion:\n{project_name}")
        self.input = QLineEdit()

        self.ok_button = QPushButton("Confirm")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_text(self):
        return self.input.text().strip()


class ClassDialog(QDialog):
    def __init__(self, title, parent=None, current_name=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(350, 200)

        layout = QVBoxLayout()

        self.input = QLineEdit()
        self.input.setText(current_name)
        self.input.setPlaceholderText("Object Name (e.g. car, person)")

        rules_label = QLabel("Object naming rules:")
        rules_label.setStyleSheet("font-weight: bold;")

        rules_list = QLabel(
            "• Must be a single word\n"
            "• Use only lowercase letters\n"
            "• No numbers or special characters\n"
            "• Descriptive and clear"
        )

        layout.addWidget(self.input)
        layout.addSpacing(10)
        layout.addWidget(rules_label)
        layout.addWidget(rules_list)
        layout.addSpacing(10)

        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("Create Object")
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def validate_and_accept(self):
        name = self.input.text().strip()
        if not re.match(r'^[a-z]+$', name):
            QMessageBox.warning(
                self,
                "Invalid Object Name",
                "Object name must:\n"
                "- Be a single word in lowercase\n"
                "- Contain only letters (no numbers or symbols)\n"
                "- Be descriptive and clear"
            )
            return
        self.accept()


class ProjectDialog(QDialog):
    def __init__(self, title, parent=None, current_name=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(350, 200)

        layout = QVBoxLayout()

        self.input = QLineEdit()
        self.input.setText(current_name)

        is_project = "Project" in title and "Subproject" not in title

        if is_project:
            self.input.setPlaceholderText("Project Name (e.g. DeepTag)")
            self.validation_pattern = r'^[A-Z][a-zA-Z]*$'
            self.error_msg = "Project name must start with uppercase letter and contain only letters!"
            rules_title = "Project naming rules:"
            rules_text = (
                "• Must start with uppercase letter\n"
                "• Contain only letters\n"
                "• Follow PascalCase convention"
            )
            btn_text = "Create Project"
        else:
            self.input.setPlaceholderText("Subproject Name (e.g. MarkClass)")
            self.validation_pattern = r'^[A-Z][a-zA-Z]*$'
            self.error_msg = "Subproject name must start with uppercase letter and contain only letters!"
            rules_title = "Subproject naming rules:"
            rules_text = (
                "• Must start with uppercase letter\n"
                "• Contain only letters\n"
                "• Follow PascalCase convention"
            )
            btn_text = "Create Subproject"

        rules_label = QLabel(rules_title)
        rules_label.setStyleSheet("font-weight: bold;")

        layout.addWidget(self.input)
        layout.addSpacing(10)
        layout.addWidget(rules_label)
        layout.addWidget(QLabel(rules_text))
        layout.addSpacing(10)

        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton(btn_text)
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def validate_and_accept(self):
        name = self.input.text().strip()
        if not name:
            QMessageBox.warning(self, "Empty Name", "Name cannot be empty!")
            return

        if not re.match(self.validation_pattern, name):
            QMessageBox.warning(self, "Invalid Name", self.error_msg)
            return

        if "Subproject" in self.windowTitle():
            parent = self.parent()
            if hasattr(parent, 'current_project') and parent.current_project:
                project_path = os.path.join("data", parent.current_project, "subprojects")
                if os.path.exists(project_path) and name in os.listdir(project_path):
                    QMessageBox.warning(self, "Duplicate Name",
                                        f"Subproject '{name}' already exists in this project!")
                    return
        self.accept()


class ProjectsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_project = None
        self.current_subproject = None
        self.current_panel = None

        self.projects_panel = None
        self.subprojects_panel = None
        self.classes_panel = None

        self.projects_list = None
        self.subprojects_list = None
        self.classes_list = None

        self.projects_add_btn = None
        self.projects_edit_btn = None
        self.projects_delete_btn = None
        self.subprojects_add_btn = None
        self.subprojects_edit_btn = None
        self.subprojects_delete_btn = None
        self.classes_add_btn = None
        self.classes_edit_btn = None
        self.classes_delete_btn = None

        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.setStyleSheet("""
            ProjectsPage {
                background-color: #f0f0f0;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 0 0 8px 8px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #f0f0f0;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;
                color: black;
            }
        """)

        top_section = QHBoxLayout()
        top_section.setSpacing(20)

        self.projects_panel = self._create_panel("Projects")
        self.subprojects_panel = self._create_panel("Subprojects")
        self.classes_panel = self._create_panel("Objects")

        top_section.addWidget(self.projects_panel)
        top_section.addWidget(self.subprojects_panel)
        top_section.addWidget(self.classes_panel)

        main_layout.addLayout(top_section)
        self.setLayout(main_layout)

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

        btn_add = QPushButton("+")
        btn_add.setToolTip("Add")
        btn_add.setStyleSheet(self._get_button_style("#4CAF50", "#3e8e41", "#43A047"))
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_edit = QPushButton("✎")
        btn_edit.setToolTip("Edit")
        btn_edit.setStyleSheet(self._get_button_style("#2196F3", "#0b7dda", "#0b7dda"))
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setEnabled(False)

        btn_delete = QPushButton("×")
        btn_delete.setToolTip("Delete")
        btn_delete.setStyleSheet(self._get_button_style("#f44336", "#d32f2f", "#d32f2f"))
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setEnabled(False)

        if title == "Projects":
            btn_add.clicked.connect(self._add_project)
            btn_edit.clicked.connect(self._edit_project)
            btn_delete.clicked.connect(self._delete_project)
            self.projects_add_btn = btn_add
            self.projects_edit_btn = btn_edit
            self.projects_delete_btn = btn_delete
        elif title == "Subprojects":
            btn_add.clicked.connect(self._add_subproject)
            btn_edit.clicked.connect(self._edit_subproject)
            btn_delete.clicked.connect(self._delete_subproject)
            self.subprojects_add_btn = btn_add
            self.subprojects_edit_btn = btn_edit
            self.subprojects_delete_btn = btn_delete
            btn_add.setEnabled(False)
        else:
            btn_add.clicked.connect(self._add_class)
            btn_edit.clicked.connect(self._edit_class)
            btn_delete.clicked.connect(self._delete_class)
            self.classes_add_btn = btn_add
            self.classes_edit_btn = btn_edit
            self.classes_delete_btn = btn_delete
            btn_add.setEnabled(False)

        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_edit)
        header_layout.addWidget(btn_delete)

        header.setLayout(header_layout)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        list_widget.itemClicked.connect(lambda item: self._on_item_clicked(item, title))

        scroll.setWidget(list_widget)
        layout.addWidget(scroll)

        if title == "Projects":
            self.projects_list = list_widget
        elif title == "Subprojects":
            self.subprojects_list = list_widget
        else:
            self.classes_list = list_widget

        container.setLayout(layout)
        return container

    def _get_button_style(self, normal_color, border_color, hover_color):
        return f"""
            QPushButton {{
                background-color: {normal_color};
                color: white;
                border: 1px solid {border_color};
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                border: 1px solid #aaaaaa;
            }}
        """

    def _on_item_clicked(self, item, panel_type):
        name = item.text()

        if panel_type == "Projects":
            self.current_project = name
            self.current_subproject = None
            self.current_panel = "Projects"

            self.projects_edit_btn.setEnabled(True)
            self.projects_delete_btn.setEnabled(True)
            self.subprojects_add_btn.setEnabled(True)

            self.subprojects_edit_btn.setEnabled(False)
            self.subprojects_delete_btn.setEnabled(False)
            self.classes_add_btn.setEnabled(False)
            self.classes_edit_btn.setEnabled(False)
            self.classes_delete_btn.setEnabled(False)

            self.load_subprojects(name)

        elif panel_type == "Subprojects":
            self.current_subproject = name
            self.current_panel = "Subprojects"

            self.subprojects_edit_btn.setEnabled(True)
            self.subprojects_delete_btn.setEnabled(True)
            self.classes_add_btn.setEnabled(True)

            self.projects_edit_btn.setEnabled(False)
            self.projects_delete_btn.setEnabled(False)
            self.classes_edit_btn.setEnabled(False)
            self.classes_delete_btn.setEnabled(False)

            self.load_classes(self.current_project, name)

        else:
            self.current_panel = "Objects"

            self.classes_edit_btn.setEnabled(True)
            self.classes_delete_btn.setEnabled(True)

            self.projects_edit_btn.setEnabled(False)
            self.projects_delete_btn.setEnabled(False)
            self.subprojects_edit_btn.setEnabled(False)
            self.subprojects_delete_btn.setEnabled(False)

        self._highlight_item(item)

    def _highlight_item(self, item):
        for list_widget in [self.projects_list, self.subprojects_list, self.classes_list]:
            for i in range(list_widget.count()):
                list_widget.item(i).setBackground(Qt.GlobalColor.white)
        item.setBackground(Qt.GlobalColor.lightGray)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._clear_selection()
        super().mousePressEvent(event)

    def _clear_selection(self):
        self.current_project = None
        self.current_subproject = None
        self.current_panel = None

        for list_widget in [self.projects_list, self.subprojects_list, self.classes_list]:
            list_widget.clearSelection()

        self.projects_edit_btn.setEnabled(False)
        self.projects_delete_btn.setEnabled(False)
        self.subprojects_add_btn.setEnabled(False)
        self.subprojects_edit_btn.setEnabled(False)
        self.subprojects_delete_btn.setEnabled(False)
        self.classes_add_btn.setEnabled(False)
        self.classes_edit_btn.setEnabled(False)
        self.classes_delete_btn.setEnabled(False)

    def _add_project(self):
        dialog = ProjectDialog("Add Project", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_name = dialog.input.text().strip()
            if project_name:
                self._save_project(project_name)
                self.load_projects()

    def _edit_project(self):
        if not self.current_project or self.current_panel != "Projects":
            return

        dialog = ProjectDialog("Edit Project", self, self.current_project)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.input.text().strip()
            if new_name and new_name != self.current_project:
                self._rename_project(self.current_project, new_name)
                self.load_projects()
                self._clear_selection()

    def _delete_project(self):
        if not self.current_project or self.current_panel != "Projects":
            return

        confirm_dialog = ConfirmationDialog(self.current_project, self)
        if confirm_dialog.exec() == QDialog.DialogCode.Accepted:
            input_name = confirm_dialog.get_text()
            if input_name != self.current_project:
                QMessageBox.warning(self, "Invalid Name", "Project name does not match!")
                return

            self._remove_project(self.current_project)
            self.load_projects()
            self.subprojects_list.clear()
            self.classes_list.clear()
            self._clear_selection()

    def _add_subproject(self):
        if not self.current_project:
            return

        dialog = ProjectDialog(f"Add Subproject to {self.current_project}", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.input.text().strip()
            if name:
                self._save_subproject(self.current_project, name)
                self.load_subprojects(self.current_project)

    def _edit_subproject(self):
        if not self.current_project or not self.current_subproject or self.current_panel != "Subprojects":
            return

        dialog = ProjectDialog("Edit Subproject", self, self.current_subproject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.input.text().strip()
            if new_name and new_name != self.current_subproject:
                self._rename_subproject(self.current_project, self.current_subproject, new_name)
                self.load_subprojects(self.current_project)
                self.current_subproject = new_name

    def _delete_subproject(self):
        if not self.current_project or not self.current_subproject or self.current_panel != "Subprojects":
            return

        confirm_dialog = QMessageBox(self)
        confirm_dialog.setWindowTitle("Confirm Delete")
        confirm_dialog.setText(f"Delete subproject '{self.current_subproject}'?")
        confirm_dialog.setInformativeText("This will also delete all objects in this subproject.")
        confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_dialog.setDefaultButton(QMessageBox.StandardButton.No)

        if confirm_dialog.exec() == QMessageBox.StandardButton.Yes:
            self._remove_subproject(self.current_project, self.current_subproject)
            self.load_subprojects(self.current_project)
            self.current_subproject = None
            self.classes_list.clear()

    def _add_class(self):
        if not self.current_project or not self.current_subproject:
            return

        dialog_title = f"Add Object to {self.current_project}/{self.current_subproject}"
        dialog = ClassDialog(dialog_title, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            class_name = dialog.input.text().strip()
            if class_name:
                self._save_class(self.current_project, self.current_subproject, class_name)
                self.load_classes(self.current_project, self.current_subproject)

    def _edit_class(self):
        if not self.current_project or not self.current_subproject or self.current_panel != "Objects":
            return

        selected_items = self.classes_list.selectedItems()
        if not selected_items:
            return

        old_name = selected_items[0].text()

        dialog_title = f"Edit Object in {self.current_project}/{self.current_subproject}"
        dialog = ClassDialog(dialog_title, self, old_name)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.input.text().strip()
            if new_name and new_name != old_name:
                self._rename_class(self.current_project, self.current_subproject, old_name, new_name)
                self.load_classes(self.current_project, self.current_subproject)

    def _delete_class(self):
        if not self.current_project or not self.current_subproject or self.current_panel != "Objects":
            return

        selected_items = self.classes_list.selectedItems()
        if not selected_items:
            return

        class_name = selected_items[0].text()

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete object '{class_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self._remove_class(self.current_project, self.current_subproject, class_name)
            self.load_classes(self.current_project, self.current_subproject)

    def _save_project(self, name):
        os.makedirs("data", exist_ok=True)
        project_path = os.path.join("data", name)
        os.makedirs(project_path, exist_ok=True)

        meta = {
            "name": name,
            "type": "project",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "subprojects": []
        }

        with open(os.path.join(project_path, "meta.json"), "w", encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

    def _rename_project(self, old_name, new_name):
        old_path = os.path.join("data", old_name)
        new_path = os.path.join("data", new_name)

        if os.path.exists(old_path):
            os.rename(old_path, new_path)

            meta_path = os.path.join(new_path, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding='utf-8') as f:
                    meta = json.load(f)
                meta["name"] = new_name
                meta["modified"] = datetime.now().isoformat()
                with open(meta_path, "w", encoding='utf-8') as f:
                    json.dump(meta, f, indent=2)

    def _remove_project(self, name):
        project_path = os.path.join("data", name)
        if os.path.exists(project_path):
            import shutil
            shutil.rmtree(project_path)

    def _save_subproject(self, project_name, subproject_name):
        project_path = os.path.join("data", project_name)
        os.makedirs(project_path, exist_ok=True)

        subprojects_path = os.path.join(project_path, "subprojects")
        os.makedirs(subprojects_path, exist_ok=True)

        subproject_path = os.path.join(subprojects_path, subproject_name)
        os.makedirs(subproject_path, exist_ok=True)

        meta_path = os.path.join(project_path, "meta.json")
        meta = {
            "name": project_name,
            "type": "project",
            "modified": datetime.now().isoformat(),
            "subprojects": []
        }

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding='utf-8') as f:
                meta = json.load(f)

        if subproject_name not in meta["subprojects"]:
            meta["subprojects"].append(subproject_name)
            meta["modified"] = datetime.now().isoformat()

            with open(meta_path, "w", encoding='utf-8') as f:
                json.dump(meta, f, indent=2)

        sub_meta = {
            "name": subproject_name,
            "type": "subproject",
            "project": project_name,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "classes": []
        }

        with open(os.path.join(subproject_path, "meta.json"), "w", encoding='utf-8') as f:
            json.dump(sub_meta, f, indent=2)

    def _rename_subproject(self, project_name, old_name, new_name):
        project_path = os.path.join("data", project_name)
        subprojects_path = os.path.join(project_path, "subprojects")

        old_path = os.path.join(subprojects_path, old_name)
        new_path = os.path.join(subprojects_path, new_name)

        if os.path.exists(old_path):
            os.rename(old_path, new_path)

            meta_path = os.path.join(project_path, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding='utf-8') as f:
                    meta = json.load(f)

                if old_name in meta["subprojects"]:
                    index = meta["subprojects"].index(old_name)
                    meta["subprojects"][index] = new_name
                    meta["modified"] = datetime.now().isoformat()

                    with open(meta_path, "w", encoding='utf-8') as f:
                        json.dump(meta, f, indent=2)

            sub_meta_path = os.path.join(new_path, "meta.json")
            if os.path.exists(sub_meta_path):
                with open(sub_meta_path, "r", encoding='utf-8') as f:
                    sub_meta = json.load(f)

                sub_meta["name"] = new_name
                sub_meta["modified"] = datetime.now().isoformat()

                with open(sub_meta_path, "w", encoding='utf-8') as f:
                    json.dump(sub_meta, f, indent=2)

    def _remove_subproject(self, project_name, subproject_name):
        project_path = os.path.join("data", project_name)
        subproject_path = os.path.join(project_path, "subprojects", subproject_name)

        if os.path.exists(subproject_path):
            import shutil
            shutil.rmtree(subproject_path)

            meta_path = os.path.join(project_path, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding='utf-8') as f:
                    meta = json.load(f)

                if subproject_name in meta["subprojects"]:
                    meta["subprojects"].remove(subproject_name)
                    meta["modified"] = datetime.now().isoformat()

                    with open(meta_path, "w", encoding='utf-8') as f:
                        json.dump(meta, f, indent=2)

    def _save_class(self, project_name, subproject_name, class_name):
        subproject_path = os.path.join("data", project_name, "subprojects", subproject_name)
        os.makedirs(subproject_path, exist_ok=True)

        meta_path = os.path.join(subproject_path, "meta.json")
        meta = {
            "name": subproject_name,
            "type": "subproject",
            "project": project_name,
            "modified": datetime.now().isoformat(),
            "classes": []
        }

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding='utf-8') as f:
                meta = json.load(f)

        if class_name not in meta["classes"]:
            meta["classes"].append(class_name)
            meta["modified"] = datetime.now().isoformat()

            with open(meta_path, "w", encoding='utf-8') as f:
                json.dump(meta, f, indent=2)

    def _rename_class(self, project_name, subproject_name, old_name, new_name):
        subproject_path = os.path.join("data", project_name, "subprojects", subproject_name)
        meta_path = os.path.join(subproject_path, "meta.json")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding='utf-8') as f:
                meta = json.load(f)

            if old_name in meta["classes"]:
                index = meta["classes"].index(old_name)
                meta["classes"][index] = new_name
                meta["modified"] = datetime.now().isoformat()

                with open(meta_path, "w", encoding='utf-8') as f:
                    json.dump(meta, f, indent=2)

    def _remove_class(self, project_name, subproject_name, class_name):
        subproject_path = os.path.join("data", project_name, "subprojects", subproject_name)
        meta_path = os.path.join(subproject_path, "meta.json")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding='utf-8') as f:
                meta = json.load(f)

            if class_name in meta["classes"]:
                meta["classes"].remove(class_name)
                meta["modified"] = datetime.now().isoformat()

                with open(meta_path, "w", encoding='utf-8') as f:
                    json.dump(meta, f, indent=2)

    def load_projects(self):
        self.projects_list.clear()

        if not os.path.exists("data"):
            return

        for item in os.listdir("data"):
            item_path = os.path.join("data", item)
            if os.path.isdir(item_path):
                meta_path = os.path.join(item_path, "meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding='utf-8') as f:
                            meta = json.load(f)
                            if meta.get("type") == "project":
                                item = QListWidgetItem(meta["name"])
                                item.setSizeHint(QSize(0, 40))
                                self.projects_list.addItem(item)
                    except json.JSONDecodeError:
                        continue

    def load_subprojects(self, project_name):
        self.subprojects_list.clear()
        self.classes_list.clear()

        if not project_name:
            return

        project_path = os.path.join("data", project_name)
        meta_path = os.path.join(project_path, "meta.json")

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding='utf-8') as f:
                    meta = json.load(f)
                    for subproject in meta.get("subprojects", []):
                        item = QListWidgetItem(subproject)
                        item.setSizeHint(QSize(0, 40))
                        self.subprojects_list.addItem(item)
            except json.JSONDecodeError:
                return

    def load_classes(self, project_name, subproject_name):
        self.classes_list.clear()

        if not project_name or not subproject_name:
            return

        subproject_path = os.path.join("data", project_name, "subprojects", subproject_name)
        meta_path = os.path.join(subproject_path, "meta.json")

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding='utf-8') as f:
                    meta = json.load(f)
                    for class_name in meta.get("classes", []):
                        item = QListWidgetItem(class_name)
                        item.setSizeHint(QSize(0, 40))
                        self.classes_list.addItem(item)
            except json.JSONDecodeError:
                return