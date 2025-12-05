"""Тесты для модуля xcode_service."""

import pytest
from telegram_xcode_bot.services.xcode_service import ProjectInfo
from telegram_xcode_bot.utils.version_utils import increment_version, increment_build_number


class TestProjectInfo:
    """Тесты для dataclass ProjectInfo."""
    
    def test_default_values(self):
        """Тест значений по умолчанию."""
        info = ProjectInfo()
        assert info.marketing_version is None
        assert info.build_version is None
        assert info.display_name is None
        assert info.bundle_id is None
        assert info.activation_date is None
    
    def test_custom_values(self):
        """Тест создания с пользовательскими значениями."""
        info = ProjectInfo(
            marketing_version="1.0",
            build_version="1",
            display_name="TestApp",
            bundle_id="com.test.app",
            activation_date="2026/01/31"
        )
        assert info.marketing_version == "1.0"
        assert info.build_version == "1"
        assert info.display_name == "TestApp"
        assert info.bundle_id == "com.test.app"
        assert info.activation_date == "2026/01/31"


class TestIncrementVersion:
    """Тесты для increment_version."""
    
    def test_simple_version(self):
        """Тест простых версий."""
        assert increment_version("1.0") == "2.0"
        assert increment_version("5.0") == "6.0"
    
    def test_complex_version(self):
        """Тест сложных версий."""
        assert increment_version("1.2.3") == "2.2.3"
        assert increment_version("5.1.2") == "6.1.2"
    
    def test_single_digit(self):
        """Тест версии из одной цифры."""
        assert increment_version("1") == "2"
        assert increment_version("9") == "10"
    
    def test_invalid_version(self):
        """Тест невалидных версий."""
        assert increment_version("abc") == "abc"  # Возвращает оригинал
        assert increment_version("") == ""


class TestIncrementBuildNumber:
    """Тесты для increment_build_number."""
    
    def test_simple_build(self):
        """Тест простых номеров билда."""
        assert increment_build_number("1") == "2"
        assert increment_build_number("10") == "11"
        assert increment_build_number("99") == "100"
    
    def test_invalid_build(self):
        """Тест невалидных номеров билда."""
        assert increment_build_number("abc") == "abc"  # Возвращает оригинал
        assert increment_build_number("") == ""

