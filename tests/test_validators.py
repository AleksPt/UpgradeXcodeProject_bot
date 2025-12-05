"""Тесты для модуля validators."""

import pytest
from telegram_xcode_bot.utils.validators import (
    validate_bundle_id,
    validate_icon_format,
    validate_icon_size,
    validate_date_format,
)


class TestValidateBundleId:
    """Тесты для validate_bundle_id."""
    
    def test_valid_bundle_ids(self):
        """Тест валидных Bundle ID."""
        assert validate_bundle_id("com.example.myapp") is True
        assert validate_bundle_id("com.company.app") is True
        assert validate_bundle_id("ru.mycompany.app123") is True
        assert validate_bundle_id("com.app-name.test") is True
    
    def test_invalid_bundle_ids(self):
        """Тест невалидных Bundle ID."""
        assert validate_bundle_id("") is False
        assert validate_bundle_id("123.example.app") is False  # Начинается с цифры
        assert validate_bundle_id("com example app") is False  # Пробелы
        assert validate_bundle_id("com.example!app") is False  # Спецсимволы
        assert validate_bundle_id(".com.example.app") is False  # Начинается с точки


class TestValidateIconFormat:
    """Тесты для validate_icon_format."""
    
    def test_valid_formats(self):
        """Тест поддерживаемых форматов."""
        assert validate_icon_format("JPEG") is True
        assert validate_icon_format("JPG") is True
        assert validate_icon_format("PNG") is True
        assert validate_icon_format("jpeg") is True
        assert validate_icon_format("jpg") is True
        assert validate_icon_format("png") is True
    
    def test_invalid_formats(self):
        """Тест неподдерживаемых форматов."""
        assert validate_icon_format("WEBP") is False
        assert validate_icon_format("GIF") is False
        assert validate_icon_format("BMP") is False
        assert validate_icon_format("") is False
        assert validate_icon_format(None) is False


class TestValidateIconSize:
    """Тесты для validate_icon_size."""
    
    def test_valid_size(self):
        """Тест правильного размера."""
        valid, error = validate_icon_size(1024, 1024)
        assert valid is True
        assert error is None
    
    def test_invalid_sizes(self):
        """Тест неправильных размеров."""
        valid, error = validate_icon_size(512, 512)
        assert valid is False
        assert "512x512" in error
        
        valid, error = validate_icon_size(2048, 2048)
        assert valid is False
        assert "2048x2048" in error
        
        valid, error = validate_icon_size(1024, 512)
        assert valid is False


class TestValidateDateFormat:
    """Тесты для validate_date_format."""
    
    def test_valid_dates(self):
        """Тест валидных форматов дат."""
        valid, error = validate_date_format("2026/01/31")
        assert valid is True
        assert error is None
        
        valid, error = validate_date_format("2025/12/25")
        assert valid is True
        assert error is None
        
        valid, error = validate_date_format("2024/06/15")
        assert valid is True
        assert error is None
    
    def test_invalid_format(self):
        """Тест невалидных форматов."""
        valid, error = validate_date_format("")
        assert valid is False
        assert "пуст" in error.lower()
        
        valid, error = validate_date_format("2026-01-31")
        assert valid is False
        assert "формат" in error.lower()
        
        valid, error = validate_date_format("31/01/2026")
        assert valid is False
        
        valid, error = validate_date_format("2026/1/31")
        assert valid is False
        
        valid, error = validate_date_format("26/01/31")
        assert valid is False
    
    def test_nonexistent_dates(self):
        """Тест несуществующих дат."""
        # 30 февраля не существует
        valid, error = validate_date_format("2025/02/30")
        assert valid is False
        assert "несуществующая" in error.lower()
        
        # 31 апреля не существует
        valid, error = validate_date_format("2025/04/31")
        assert valid is False
        assert "несуществующая" in error.lower()
        
        # 29 февраля в невисокосном году
        valid, error = validate_date_format("2025/02/29")
        assert valid is False
        assert "несуществующая" in error.lower()
    
    def test_leap_year(self):
        """Тест високосного года."""
        # 29 февраля в високосном году должно быть валидно
        valid, error = validate_date_format("2024/02/29")
        assert valid is True
        assert error is None

