from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from app.utils.logger import log
from app.ui.home import HomePage
from app.ui.stats import StatsPage
from app.ui.annotate import AnnotatePage
from app.ui.projects import ProjectsPage
from app.ui.settings import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        log("INIT", "Initializing MainWindow")
        self.setWindowTitle("DeepTag")

        self.stacked_widget = QStackedWidget()
        self.pages = {}
        self.nav_buttons = {}

        self.setup_ui()
        log("INIT", "MainWindow initialization completed")

    def setup_ui(self):
        log("UI", "Starting main UI setup")
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_bar = self.create_navigation_bar()
        log("UI", "Navigation bar created")

        self.setup_pages()
        log("UI", "Pages setup completed")

        main_layout.addWidget(nav_bar)
        main_layout.addWidget(self.stacked_widget)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        log("UI", "Main layout finalized")

    def create_navigation_bar(self):
        log("UI", "Creating navigation bar")
        nav_bar = QFrame()
        nav_bar.setObjectName("navBar")

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(10, 5, 10, 5)
        nav_layout.setSpacing(5)

        buttons = [
            ("home", "🏠 Home"),
            ("projects", "📂 Projects"),
            ("markup", "✏️ Annotate"),
            ("stats", "📊 Stats"),
            ("settings", "⚙ Settings")
        ]

        log("UI", f"Creating {len(buttons)} navigation buttons")
        for page_id, text in buttons:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda _, p=page_id: self.switch_page(p))

            self.nav_buttons[page_id] = btn
            nav_layout.addWidget(btn)
            log("UI", f"Added button: {text} (ID: {page_id})")

        if "settings" in self.nav_buttons:
            nav_layout.insertStretch(nav_layout.count() - 1, 1)
            log("UI", "Added stretch before settings button")

        nav_bar.setLayout(nav_layout)
        return nav_bar

    def setup_pages(self):
        log("PAGES", "Initializing application pages")
        self.pages = {
            "home": HomePage(),
            "projects": ProjectsPage(),
            "markup": AnnotatePage(),
            "stats": StatsPage(),
            "settings": SettingsPage()
        }

        for page_id, page in self.pages.items():
            self.stacked_widget.addWidget(page)
            log("PAGES", f"Added page to stack: {page_id} ({type(page).__name__})")

        self.switch_page("home")
        log("NAV", "Initial page set to: home")

    def switch_page(self, page_id):
        old_page = self.stacked_widget.currentWidget()
        old_page_name = type(old_page).__name__ if old_page else "None"

        log("NAV", f"Switching page from {old_page_name} to {page_id}")
        self.stacked_widget.setCurrentWidget(self.pages[page_id])

        for btn_id, btn in self.nav_buttons.items():
            prev_state = btn.isChecked()
            new_state = btn_id == page_id
            btn.setChecked(new_state)
            if prev_state != new_state:
                log("NAV", f"Button {btn_id} state changed: {prev_state} → {new_state}")

        current_page = type(self.pages[page_id]).__name__
        log("NAV", f"Navigation completed. Current page: {current_page}")
