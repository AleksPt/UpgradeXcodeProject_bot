"""Централизованное логирование для Telegram Xcode Bot."""

import logging
import sys
from typing import Optional

# Настройка формата логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(
    name: str = __name__,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Настраивает и возвращает logger с заданными параметрами.
    
    Args:
        name: Имя logger'а
        level: Уровень логирования (по умолчанию INFO)
        format_string: Формат логов (по умолчанию LOG_FORMAT)
    
    Returns:
        Настроенный logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Удаляем существующие handlers, чтобы избежать дубликатов
    logger.handlers.clear()
    
    # Создаем handler для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Устанавливаем формат
    formatter = logging.Formatter(
        format_string or LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# Глобальный logger для всего приложения
logger = setup_logger('telegram_xcode_bot')


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает logger с заданным именем.
    
    Args:
        name: Имя logger'а
    
    Returns:
        Logger с заданным именем
    """
    return logging.getLogger(f'telegram_xcode_bot.{name}')

