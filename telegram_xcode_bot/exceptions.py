"""Кастомные исключения для Telegram Xcode Bot."""

from typing import Optional


class BotError(Exception):
    """Базовое исключение для всех ошибок бота."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Args:
            message: Основное сообщение об ошибке
            details: Дополнительные детали ошибки
        """
        self.message = message
        self.details = details
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\nДетали: {self.details}"
        return self.message


class XcodeProjectError(BotError):
    """Ошибка при работе с Xcode проектом."""
    pass


class ArchiveProcessingError(BotError):
    """Ошибка при обработке архива."""
    pass


class ValidationError(BotError):
    """Ошибка валидации данных."""
    pass


class IconProcessingError(BotError):
    """Ошибка при обработке иконки."""
    pass


class ConfigurationError(BotError):
    """Ошибка конфигурации бота."""
    pass

