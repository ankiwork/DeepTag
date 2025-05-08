from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from app.ui.home import HomePage
from app.ui.stats import StatsPage
from app.ui.annotate import AnnotatePage
from app.ui.projects import ProjectsPage
from app.ui.settings import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application")

        self.stacked_widget = QStackedWidget()
        self.pages = {}
        self.nav_buttons = {}

        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_bar = self.create_navigation_bar()

        self.setup_pages()

        main_layout.addWidget(nav_bar)
        main_layout.addWidget(self.stacked_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_navigation_bar(self):
        nav_bar = QFrame()
        nav_bar.setObjectName("navBar")

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 5, 10, 5)
        nav_layout.setSpacing(5)

        nav_bar.setStyleSheet("""
            /* Main navigation bar - чистый белый фон */
            QFrame#navBar {
                background-color: #ffffff;
                border: none;
                margin: 0;
            }

            /* Base button style */
            QPushButton#navButton {
                background-color: transparent;
                border: none;
                padding: 8px 16px;  /* Более компактные кнопки */
                color: #555555;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                border-radius: 4px;
                min-width: 60px;  /* Уменьшенная минимальная ширина */
            }

            /* Hover effect */
            QPushButton#navButton:hover {
                background-color: #f5f5f5;
            }

            /* Pressed/active button */
            QPushButton#navButton:checked {
                background-color: #e0e0e0;
                color: #222222;
                font-weight: 500;
            }
        """)

        buttons = [
            ("home", "🏠 Home"),
            ("projects", "📂 Projects"),
            ("markup", "✏️ Annotate"),
            ("stats", "📊 Stats"),
            ("settings", "⚙ Settings")
        ]

        for page_id, text in buttons:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda _, p=page_id: self.switch_page(p))

            self.nav_buttons[page_id] = btn
            nav_layout.addWidget(btn)

        if "settings" in self.nav_buttons:
            nav_layout.insertStretch(nav_layout.count() - 1, 1)

        nav_bar.setLayout(nav_layout)
        return nav_bar

    def setup_pages(self):
        self.pages = {
            "home": HomePage(),
            "projects": ProjectsPage(),
            "markup": AnnotatePage(),
            "stats": StatsPage(),
            "settings": SettingsPage()
        }

        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        self.switch_page("home")

    def switch_page(self, page_id):
        self.stacked_widget.setCurrentWidget(self.pages[page_id])
        for btn_id, btn in self.nav_buttons.items():
            btn.setChecked(btn_id == page_id)
