"""Тесты для модуля version_utils."""

import pytest
from telegram_xcode_bot.utils.version_utils import (
    increment_version,
    increment_build_number,
    parse_version,
)


class TestIncrementVersion:
    """Тесты для increment_version."""
    
    def test_simple_version(self):
        """Тест простых версий."""
        assert increment_version("1.0") == "2.0"
        assert increment_version("5.0") == "6.0"
        assert increment_version("9.5") == "10.5"
    
    def test_complex_version(self):
        """Тест сложных версий."""
        assert increment_version("1.2.3") == "2.2.3"
        assert increment_version("5.1.2") == "6.1.2"
        assert increment_version("0.9.1") == "1.9.1"
    
    def test_single_digit(self):
        """Тест версии из одной цифры."""
        assert increment_version("1") == "2"
        assert increment_version("9") == "10"
        assert increment_version("99") == "100"
    
    def test_invalid_version(self):
        """Тест невалидных версий."""
        assert increment_version("abc") == "abc"
        assert increment_version("") == ""
        assert increment_version("v1.0") == "v1.0"


class TestIncrementBuildNumber:
    """Тесты для increment_build_number."""
    
    def test_simple_build(self):
        """Тест простых номеров билда."""
        assert increment_build_number("1") == "2"
        assert increment_build_number("10") == "11"
        assert increment_build_number("99") == "100"
    
    def test_large_build_number(self):
        """Тест больших номеров билда."""
        assert increment_build_number("999") == "1000"
        assert increment_build_number("1234") == "1235"
    
    def test_invalid_build(self):
        """Тест невалидных номеров билда."""
        assert increment_build_number("abc") == "abc"
        assert increment_build_number("") == ""
        assert increment_build_number("1.2") == "1.2"


class TestParseVersion:
    """Тесты для parse_version."""
    
    def test_parse_simple_version(self):
        """Тест парсинга простой версии."""
        assert parse_version("1.0") == (1, 0)
        assert parse_version("2.5") == (2, 5)
    
    def test_parse_complex_version(self):
        """Тест парсинга сложной версии."""
        assert parse_version("1.2.3") == (1, 2, 3)
        assert parse_version("10.20.30") == (10, 20, 30)
    
    def test_parse_single_digit(self):
        """Тест парсинга одиночной цифры."""
        assert parse_version("5") == (5,)
    
    def test_parse_invalid_version(self):
        """Тест парсинга невалидной версии."""
        assert parse_version("abc") is None
        assert parse_version("1.a.3") is None
        assert parse_version("") is None

