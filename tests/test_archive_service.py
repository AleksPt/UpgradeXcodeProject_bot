"""Тесты для модуля archive_service."""

import pytest
import os
import tempfile
import zipfile
from pathlib import Path

from telegram_xcode_bot.services.archive_service import (
    extract_archive,
    create_archive,
)
from telegram_xcode_bot.exceptions import ArchiveProcessingError


class TestExtractArchive:
    """Тесты для extract_archive."""
    
    def test_extract_valid_archive(self, temp_dir):
        """Тест успешной распаковки валидного архива."""
        # Создаем тестовый архив
        archive_path = temp_dir / "test.zip"
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        
        # Создаем файл для архивирования
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.write(test_file, "test.txt")
        
        # Распаковываем
        extract_archive(str(archive_path), str(extract_dir))
        
        # Проверяем
        assert (extract_dir / "test.txt").exists()
        assert (extract_dir / "test.txt").read_text() == "test content"
    
    def test_extract_corrupted_archive(self, temp_dir):
        """Тест обработки поврежденного архива."""
        # Создаем поврежденный файл
        corrupted_path = temp_dir / "corrupted.zip"
        corrupted_path.write_text("not a zip file")
        
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        
        # Должно выбросить исключение
        with pytest.raises(ArchiveProcessingError) as exc_info:
            extract_archive(str(corrupted_path), str(extract_dir))
        
        assert "Поврежденный zip архив" in str(exc_info.value)
    
    def test_extract_archive_with_path_traversal(self, temp_dir):
        """Тест защиты от path traversal атаки."""
        # Создаем архив с path traversal
        archive_path = temp_dir / "malicious.zip"
        extract_dir = temp_dir / "extract"
        extract_dir.mkdir()
        
        with zipfile.ZipFile(archive_path, 'w') as zf:
            # Пытаемся добавить файл с path traversal
            zf.writestr("../../../etc/passwd", "malicious content")
        
        # Должно выбросить исключение
        with pytest.raises(ArchiveProcessingError) as exc_info:
            extract_archive(str(archive_path), str(extract_dir))
        
        assert "потенциально опасный путь" in str(exc_info.value).lower()


class TestCreateArchive:
    """Тесты для create_archive."""
    
    def test_create_archive_success(self, temp_dir):
        """Тест успешного создания архива."""
        # Создаем директорию с файлами
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        
        (source_dir / "file1.txt").write_text("content 1")
        (source_dir / "file2.txt").write_text("content 2")
        
        # Создаем поддиректорию
        subdir = source_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content 3")
        
        # Создаем архив
        output_path = temp_dir / "output.zip"
        create_archive(str(source_dir), str(output_path))
        
        # Проверяем архив
        assert output_path.exists()
        
        # Проверяем содержимое архива
        with zipfile.ZipFile(output_path, 'r') as zf:
            names = zf.namelist()
            assert "file1.txt" in names
            assert "file2.txt" in names
            assert "subdir/file3.txt" in names or "subdir\\file3.txt" in names
    
    def test_create_archive_empty_directory(self, temp_dir):
        """Тест создания архива из пустой директории."""
        source_dir = temp_dir / "empty"
        source_dir.mkdir()
        
        output_path = temp_dir / "empty.zip"
        create_archive(str(source_dir), str(output_path))
        
        assert output_path.exists()
        
        with zipfile.ZipFile(output_path, 'r') as zf:
            assert len(zf.namelist()) == 0

