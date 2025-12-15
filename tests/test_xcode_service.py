"""Тесты для модуля xcode_service."""

import pytest
import tempfile
import os
from telegram_xcode_bot.services.xcode_service import ProjectInfo, _update_plist_usage_descriptions
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


class TestUpdatePlistUsageDescriptions:
    """Тесты для _update_plist_usage_descriptions."""
    
    def test_update_camera_and_photo_descriptions(self):
        """Тест обновления описаний камеры и фотобиблиотеки."""
        # Создаем временный Info.plist с тестовым содержимым
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSCameraUsageDescription</key>
    <string>The OldApp application requests access to your Camera for adding a photo</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>The OldApp application requests access to your Photo Library for adding an image</string>
</dict>
</plist>"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.plist', encoding='utf-8') as f:
            f.write(plist_content)
            temp_path = f.name
        
        try:
            # Обновляем описания
            result = _update_plist_usage_descriptions(temp_path, "BestGame")
            assert result is True
            
            # Проверяем обновленное содержимое
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            assert "The BestGame application requests access to your Camera for adding a photo" in updated_content
            assert "The BestGame application requests access to your Photo Library for adding an image" in updated_content
            assert "The OldApp application" not in updated_content
        finally:
            os.unlink(temp_path)
    
    def test_update_with_multiline_format(self):
        """Тест обновления с многострочным форматом."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSCameraUsageDescription</key>
    <string>The TestApp application requests access to your Camera for adding a photo</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>The TestApp application requests access to your Photo Library for adding an image</string>
</dict>
</plist>"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.plist', encoding='utf-8') as f:
            f.write(plist_content)
            temp_path = f.name
        
        try:
            result = _update_plist_usage_descriptions(temp_path, "MyNewApp")
            assert result is True
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            assert "The MyNewApp application requests access to your Camera for adding a photo" in updated_content
            assert "The MyNewApp application requests access to your Photo Library for adding an image" in updated_content
        finally:
            os.unlink(temp_path)
    
    def test_no_update_when_keys_missing(self):
        """Тест, что функция возвращает False если ключи отсутствуют."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>TestApp</string>
</dict>
</plist>"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.plist', encoding='utf-8') as f:
            f.write(plist_content)
            temp_path = f.name
        
        try:
            result = _update_plist_usage_descriptions(temp_path, "NewApp")
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_update_with_special_characters_in_name(self):
        """Тест обновления с специальными символами в названии."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSCameraUsageDescription</key>
    <string>The OldApp application requests access to your Camera for adding a photo</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>The OldApp application requests access to your Photo Library for adding an image</string>
</dict>
</plist>"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.plist', encoding='utf-8') as f:
            f.write(plist_content)
            temp_path = f.name
        
        try:
            result = _update_plist_usage_descriptions(temp_path, "App's & Co.")
            assert result is True
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            assert "The App's & Co. application requests access to your Camera for adding a photo" in updated_content
            assert "The App's & Co. application requests access to your Photo Library for adding an image" in updated_content
        finally:
            os.unlink(temp_path)

