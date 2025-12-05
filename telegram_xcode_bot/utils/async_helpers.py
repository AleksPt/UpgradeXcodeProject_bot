"""Вспомогательные функции для асинхронных операций."""

import asyncio
from functools import wraps
from typing import Callable, Any, TypeVar, ParamSpec

from telegram_xcode_bot.config import PROCESS_TIMEOUT_SECONDS
from telegram_xcode_bot.logger import get_logger

logger = get_logger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def run_with_timeout(func: Callable[P, T], timeout: float = PROCESS_TIMEOUT_SECONDS) -> Callable[P, T]:
    """
    Декоратор для выполнения синхронной функции с тайм-аутом в executor.
    
    Args:
        func: Функция для выполнения
        timeout: Тайм-аут в секундах
    
    Returns:
        Wrapper функция
    """
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: func(*args, **kwargs)),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Timeout executing {func.__name__} after {timeout}s")
            raise TimeoutError(f"Операция {func.__name__} превысила время ожидания ({timeout}s)")
    
    return wrapper


async def run_blocking_io(func: Callable[P, T], *args: P.args, timeout: float = PROCESS_TIMEOUT_SECONDS, **kwargs: P.kwargs) -> T:
    """
    Выполняет блокирующую IO операцию в executor с тайм-аутом.
    
    Args:
        func: Синхронная функция для выполнения
        *args: Позиционные аргументы функции
        timeout: Тайм-аут в секундах
        **kwargs: Именованные аргументы функции
    
    Returns:
        Результат выполнения функции
    
    Raises:
        TimeoutError: Если операция превысила тайм-аут
    """
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: func(*args, **kwargs)),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Timeout executing {func.__name__} after {timeout}s")
        raise TimeoutError(f"Операция превысила время ожидания ({timeout}s)")

