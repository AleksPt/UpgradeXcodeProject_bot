"""Rate limiter для защиты от спама."""

from time import time
from collections import defaultdict
from typing import Dict, List

from telegram_xcode_bot.config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
from telegram_xcode_bot.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Простой rate limiter на основе sliding window.
    
    Отслеживает количество запросов от каждого пользователя
    и блокирует, если превышен лимит.
    """
    
    def __init__(
        self,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS
    ):
        """
        Инициализация rate limiter.
        
        Args:
            max_requests: Максимальное количество запросов
            window_seconds: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[int, List[float]] = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Проверяет, разрешен ли запрос для пользователя.
        
        Args:
            user_id: ID пользователя
        
        Returns:
            True если запрос разрешен, False если превышен лимит
        """
        now = time()
        
        # Очищаем старые запросы за пределами временного окна
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window_seconds
        ]
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{len(self.requests[user_id])} requests in {self.window_seconds}s"
            )
            return False
        
        # Добавляем новый запрос
        self.requests[user_id].append(now)
        return True
    
    def reset_user(self, user_id: int) -> None:
        """
        Сбрасывает счетчик для конкретного пользователя.
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.requests:
            del self.requests[user_id]
            logger.info(f"Rate limit reset for user {user_id}")
    
    def get_remaining_requests(self, user_id: int) -> int:
        """
        Возвращает количество оставшихся запросов для пользователя.
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Количество оставшихся запросов
        """
        now = time()
        
        # Очищаем старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[user_id]))


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()

