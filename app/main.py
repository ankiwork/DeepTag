import sys
from PySide6.QtWidgets import QApplication

from app.build import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("app/styles/style.css", "r") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
