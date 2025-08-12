import os
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Общая функция для создания логгеров
def create_logger(name: str, log_file: str, level=logging.INFO):
    log_path = os.path.join(LOG_DIR, log_file)

    # Добавлена кодировка UTF-8
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)

    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    stream_handler.setFormatter(stream_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logger.propagate = False
    return logger

# Логгеры
downloading_data_logger = create_logger("downloading_data_logger", "downloading_data_logger.log")
filter_futures_logger = create_logger("filter_futures_logger", "filter_futures_logger.log")
