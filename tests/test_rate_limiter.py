"""Тесты для модуля rate_limiter."""

import pytest
from time import sleep

from telegram_xcode_bot.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    """Тесты для RateLimiter."""
    
    def test_allows_requests_within_limit(self):
        """Тест что запросы в пределах лимита разрешены."""
        limiter = RateLimiter(max_requests=3, window_seconds=10)
        user_id = 123
        
        # Первые 3 запроса должны быть разрешены
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
    
    def test_blocks_requests_over_limit(self):
        """Тест что запросы сверх лимита блокируются."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        user_id = 456
        
        # Первые 2 запроса разрешены
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        
        # Третий запрос должен быть заблокирован
        assert limiter.is_allowed(user_id) is False
    
    def test_different_users_independent(self):
        """Тест что разные пользователи не влияют друг на друга."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        user1 = 111
        user2 = 222
        
        # User 1 делает 2 запроса
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user1) is True
        
        # User 2 должен иметь свой лимит
        assert limiter.is_allowed(user2) is True
        assert limiter.is_allowed(user2) is True
        
        # Оба превысили лимит
        assert limiter.is_allowed(user1) is False
        assert limiter.is_allowed(user2) is False
    
    def test_reset_user(self):
        """Тест сброса счетчика для пользователя."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        user_id = 789
        
        # Исчерпываем лимит
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        assert limiter.is_allowed(user_id) is False
        
        # Сбрасываем
        limiter.reset_user(user_id)
        
        # Теперь снова должно быть разрешено
        assert limiter.is_allowed(user_id) is True
    
    def test_get_remaining_requests(self):
        """Тест получения количества оставшихся запросов."""
        limiter = RateLimiter(max_requests=5, window_seconds=10)
        user_id = 999
        
        # Вначале должно быть 5 запросов
        assert limiter.get_remaining_requests(user_id) == 5
        
        # После одного запроса - 4
        limiter.is_allowed(user_id)
        assert limiter.get_remaining_requests(user_id) == 4
        
        # После двух - 3
        limiter.is_allowed(user_id)
        assert limiter.get_remaining_requests(user_id) == 3
    
    def test_window_expiration(self):
        """Тест что старые запросы истекают после временного окна."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        user_id = 555
        
        # Исчерпываем лимит
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        assert limiter.is_allowed(user_id) is False
        
        # Ждем истечения окна
        sleep(1.1)
        
        # Теперь снова должно быть разрешено
        assert limiter.is_allowed(user_id) is True

