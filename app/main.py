import sys
from PySide6.QtWidgets import QApplication

from app.build import MainWindow
from app.utils.logger import log


if __name__ == "__main__":
    try:
        log("SYSTEM", "Starting application initialization")
        log("ENV", f"Python version: {sys.version}")
        log("ENV", f"Executable path: {sys.executable}")

        log("QT", "Creating QApplication instance")
        app = QApplication(sys.argv)

        try:
            style_path = "app/styles/style.css"
            log("STYLE", f"Loading styles from: {style_path}")
            with open(style_path, "r") as f:
                styles = f.read()
                app.setStyleSheet(styles)
                log("STYLE", f"Successfully loaded {len(styles)} characters of CSS")
        except FileNotFoundError:
            log("ERROR", f"Stylesheet not found: {style_path}")
        except Exception as e:
            log("ERROR", f"Error loading stylesheet: {str(e)}")

        try:
            log("WINDOW", "Creating MainWindow instance")
            window = MainWindow()
            log("WINDOW", "MainWindow created successfully")

            log("WINDOW", "Showing window maximized")
            window.showMaximized()
            log("UI", "Window displayed in maximized state")
        except Exception as e:
            log("ERROR", f"Failed to create main window: {str(e)}")
            sys.exit(1)

        log("APP", "Starting application event loop")
        exit_code = app.exec()
        log("APP", f"Application exited with code: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        log("CRITICAL", f"Unhandled exception: {str(e)}")
        sys.exit(1)
