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
        assert validate_date_format("2026/01/31") is True
        assert validate_date_format("2025/12/25") is True
        assert validate_date_format("2024/06/15") is True
    
    def test_invalid_dates(self):
        """Тест невалидных форматов дат."""
        assert validate_date_format("") is False
        assert validate_date_format("2026-01-31") is False  # Неправильный разделитель
        assert validate_date_format("31/01/2026") is False  # Неправильный порядок
        assert validate_date_format("2026/1/31") is False  # Неполный формат
        assert validate_date_format("26/01/31") is False  # Неполный год

