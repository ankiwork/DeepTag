from PySide6.QtCore import Qt
from PySide6.QtWidgets import *


class AnnotatePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.setStyleSheet("""
            ProjectsPage {
                background-color: #f0f0f0;
            }
        """)

        top_section = QHBoxLayout()
        top_section.setSpacing(20)

        panel_titles = ["Allocate", "Process", "Dataset"]
        for title in panel_titles:
            panel = self._create_panel(title)
            top_section.addWidget(panel)

        main_layout.addLayout(top_section)

        main_layout.setStretch(0, 1)

        self.setLayout(main_layout)

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
        layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Fixed alignment
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
        layout.addWidget(title_label)

        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        layout.addWidget(content)

        layout.setStretch(1, 1)

        container.setLayout(layout)
        return container
