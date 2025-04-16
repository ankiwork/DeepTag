import json
import logging
from pathlib import Path
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """Форматирует логи в JSON-формат."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


def setup_logger(name: str, log_file: Path) -> logging.Logger:
    """Настраивает и возвращает логгер."""

    # Создаем директорию для логов, если её нет
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Обработчик для записи в файл (JSON-формат)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.DEBUG)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    console_handler.setLevel(logging.INFO)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
