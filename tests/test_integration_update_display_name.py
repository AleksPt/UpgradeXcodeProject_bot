"""Интеграционные тесты для обновления названия приложения."""

import os
import tempfile
import zipfile
from pathlib import Path

import pytest

from telegram_xcode_bot.services.xcode_service import update_display_name
from telegram_xcode_bot.services.archive_service import process_archive_with_actions


class TestIntegrationUpdateDisplayName:
    """Интеграционные тесты для обновления display name с Info.plist."""
    
    def test_update_display_name_updates_pbxproj(self):
        """Тест, что update_display_name обновляет project.pbxproj."""
        # Создаем временную структуру проекта
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "TestApp"
            project_dir.mkdir()
            
            # Создаем структуру Xcode проекта
            xcode_proj = project_dir / "TestApp.xcodeproj"
            xcode_proj.mkdir()
            
            # Создаем project.pbxproj
            pbxproj_content = """
// !$*UTF8*$!
{
    archiveVersion = 1;
    classes = {
    };
    objectVersion = 56;
    objects = {
        INFOPLIST_KEY_CFBundleDisplayName = "OldApp";
        PRODUCT_BUNDLE_IDENTIFIER = com.test.oldapp;
        MARKETING_VERSION = 1.0;
        CURRENT_PROJECT_VERSION = 1;
    };
    rootObject = 1234567890ABCDEF12345678;
}
"""
            pbxproj_path = xcode_proj / "project.pbxproj"
            with open(pbxproj_path, 'w', encoding='utf-8') as f:
                f.write(pbxproj_content)
            
            # Обновляем display name
            result = update_display_name(str(pbxproj_path), "BestGame")
            assert result is True
            
            # Проверяем, что project.pbxproj обновлен
            with open(pbxproj_path, 'r', encoding='utf-8') as f:
                pbxproj_updated = f.read()
            assert 'INFOPLIST_KEY_CFBundleDisplayName = "BestGame";' in pbxproj_updated
            assert 'INFOPLIST_KEY_CFBundleDisplayName = "OldApp";' not in pbxproj_updated
    
    def test_process_archive_with_name_change_action(self):
        """Тест полного процесса обработки архива с изменением названия."""
        # Создаем временную структуру проекта
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "TestProject"
            project_dir.mkdir()
            
            # Создаем Xcode проект
            xcode_proj = project_dir / "TestApp.xcodeproj"
            xcode_proj.mkdir()
            
            pbxproj_content = """// !$*UTF8*$!
{
    INFOPLIST_KEY_CFBundleDisplayName = "OriginalApp";
    MARKETING_VERSION = 1.0;
    CURRENT_PROJECT_VERSION = 1;
}"""
            pbxproj_path = xcode_proj / "project.pbxproj"
            with open(pbxproj_path, 'w', encoding='utf-8') as f:
                f.write(pbxproj_content)
            
            # Создаем Info.plist
            plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSCameraUsageDescription</key>
    <string>Original camera description</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>Original photo library description</string>
</dict>
</plist>"""
            plist_path = project_dir / "Info.plist"
            with open(plist_path, 'w', encoding='utf-8') as f:
                f.write(plist_content)
            
            # Создаем zip архив
            input_zip = Path(temp_dir) / "input.zip"
            with zipfile.ZipFile(input_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arc_name)
            
            # Обрабатываем архив
            output_zip = Path(temp_dir) / "output.zip"
            actions = {
                'increment_version': False,
                'new_name': 'SuperApp',
                'new_bundle_id': None,
                'new_icon_path': None,
                'new_activation_date': None,
                'add_ipad': False
            }
            
            result = process_archive_with_actions(str(input_zip), str(output_zip), actions)
            
            assert result.success is True
            assert result.project_info.display_name == "SuperApp"
            
            # Распаковываем результат и проверяем
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            with zipfile.ZipFile(output_zip, 'r') as zipf:
                zipf.extractall(output_dir)
            
            # Проверяем project.pbxproj
            output_pbxproj = output_dir / "TestProject" / "TestApp.xcodeproj" / "project.pbxproj"
            with open(output_pbxproj, 'r', encoding='utf-8') as f:
                content = f.read()
            assert 'INFOPLIST_KEY_CFBundleDisplayName = "SuperApp";' in content
            
            # Проверяем, что Info.plist НЕ изменился
            output_plist = output_dir / "TestProject" / "Info.plist"
            with open(output_plist, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "Original camera description" in content
            assert "Original photo library description" in content

