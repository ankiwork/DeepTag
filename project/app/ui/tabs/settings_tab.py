import logging
from pathlib import Path
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

from project.app.utils.logger import setup_logger


def _change_theme(theme_name: str, logger: logging.Logger) -> None:
    """Изменяет тему оформления приложения.

    Args:
        theme_name: Название выбранной темы
        logger: Логгер для записи событий
    """
    logger.info(f"Попытка изменения темы на: {theme_name}")
    message = QMessageBox()
    message.setWindowTitle("В разработке")
    message.setText("Выбор темы временно недоступен\nЭта функция находится в активной разработке")
    message.setIcon(QMessageBox.Icon.Information)
    message.exec()
    logger.warning("Функционал смены темы временно недоступен")


def _change_language(language: str, logger: logging.Logger) -> None:
    """Изменяет язык интерфейса.

    Args:
        language: Выбранный язык интерфейса
        logger: Логгер для записи событий
    """
    logger.info(f"Попытка изменения языка на: {language}")
    message = QMessageBox()
    message.setWindowTitle("В разработке")
    message.setText("Выбор языка временно недоступен\nЭта функция находится в активной разработке")
    message.setIcon(QMessageBox.Icon.Information)
    message.exec()
    logger.warning("Функционал смены языка временно недоступен")


class SettingsTab(QWidget):
    """Вкладка настроек приложения с возможностью смены темы и языка."""

    def __init__(self):
        super().__init__()
        self.log_file = Path(__file__).parent.parent.parent / "logs" / "settings.log"

        # Инициализация логгера
        self.logger = setup_logger("SettingsTab", self.log_file)
        self.logger.info("Инициализация компонента SettingsTab")

        self.translator = QTranslator()
        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        """Инициализация пользовательского интерфейса."""
        self.logger.debug("Начало инициализации пользовательского интерфейса")

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Заголовок "В разработке"
        dev_label = QLabel("⚙️ Настройки в разработке ⚙️")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_label.setStyleSheet("font-size: 16px; color: #666; font-weight: bold;")
        main_layout.addWidget(dev_label)

        # Секции настроек
        self._setup_theme_section(main_layout)
        self._setup_language_section(main_layout)

        # Пояснительный текст
        info_label = QLabel("Эти функции временно недоступны\nи находятся в активной разработке")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #888; font-size: 12px;")
        main_layout.addWidget(info_label)

        self.setLayout(main_layout)
        self.logger.debug("Завершение инициализации пользовательского интерфейса")

    def _setup_theme_section(self, layout: QVBoxLayout) -> None:
        """Настраивает секцию выбора темы оформления."""
        self.logger.debug("Инициализация секции выбора темы")

        theme_label = QLabel("Тема оформления:")
        theme_label.setEnabled(False)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.currentTextChanged.connect(
            lambda: _change_theme(self.theme_combo.currentText(), self.logger)
        )
        self.theme_combo.setEnabled(False)
        self.theme_combo.setStyleSheet("QComboBox { background-color: #f0f0f0; }")

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        layout.addLayout(theme_layout)

    def _setup_language_section(self, layout: QVBoxLayout) -> None:
        """Настраивает секцию выбора языка интерфейса."""
        self.logger.debug("Инициализация секции выбора языка")

        language_label = QLabel("Язык интерфейса:")
        language_label.setEnabled(False)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Русский", "English"])
        self.language_combo.currentTextChanged.connect(
            lambda: _change_language(self.language_combo.currentText(), self.logger)
        )
        self.language_combo.setEnabled(False)
        self.language_combo.setStyleSheet("QComboBox { background-color: #f0f0f0; }")

        language_layout = QHBoxLayout()
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()

        layout.addLayout(language_layout)

    def _load_settings(self) -> None:
        """Загружает и применяет сохранённые настройки."""
        self.logger.debug("Загрузка настроек приложения")
        try:
            self.theme_combo.setCurrentText("Светлая")
            self.language_combo.setCurrentText("Русский")
            self.logger.info("Применены настройки по умолчанию")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке настроек: {str(e)}", exc_info=True)
            QMessageBox.warning(
                self,
                "Ошибка",
                "Не удалось загрузить настройки. Применены значения по умолчанию."
            )
