"""Тесты для модуля icon_service."""

import pytest
import json
from pathlib import Path
from PIL import Image

from telegram_xcode_bot.services.icon_service import (
    validate_icon,
    convert_png_to_jpeg,
)
from telegram_xcode_bot.exceptions import IconProcessingError


class TestValidateIcon:
    """Тесты для validate_icon."""
    
    def test_valid_jpeg_icon(self, temp_dir):
        """Тест валидной JPEG иконки."""
        # Создаем тестовое изображение 1024x1024
        img = Image.new('RGB', (1024, 1024), color='red')
        img_path = temp_dir / "icon.jpg"
        img.save(img_path, 'JPEG')
        
        valid, error = validate_icon(str(img_path))
        assert valid is True
        assert error is None
    
    def test_valid_png_icon(self, temp_dir):
        """Тест валидной PNG иконки."""
        img = Image.new('RGB', (1024, 1024), color='blue')
        img_path = temp_dir / "icon.png"
        img.save(img_path, 'PNG')
        
        valid, error = validate_icon(str(img_path))
        assert valid is True
        assert error is None
    
    def test_invalid_size(self, temp_dir):
        """Тест изображения неправильного размера."""
        img = Image.new('RGB', (512, 512), color='green')
        img_path = temp_dir / "small_icon.jpg"
        img.save(img_path, 'JPEG')
        
        valid, error = validate_icon(str(img_path))
        assert valid is False
        assert "512x512" in error
        assert "1024x1024" in error
    
    def test_invalid_format(self, temp_dir):
        """Тест неподдерживаемого формата."""
        img = Image.new('RGB', (1024, 1024), color='yellow')
        img_path = temp_dir / "icon.bmp"
        img.save(img_path, 'BMP')
        
        valid, error = validate_icon(str(img_path))
        assert valid is False
        assert "BMP" in error or "формат" in error.lower()


class TestConvertPngToJpeg:
    """Тесты для convert_png_to_jpeg."""
    
    def test_convert_rgb_png(self, temp_dir):
        """Тест конвертации RGB PNG в JPEG."""
        # Создаем RGB PNG
        img = Image.new('RGB', (100, 100), color='red')
        png_path = temp_dir / "test.png"
        img.save(png_path, 'PNG')
        
        # Конвертируем
        jpeg_path = temp_dir / "test.jpg"
        convert_png_to_jpeg(str(png_path), str(jpeg_path))
        
        # Проверяем
        assert jpeg_path.exists()
        result_img = Image.open(jpeg_path)
        assert result_img.format == 'JPEG'
        assert result_img.size == (100, 100)
    
    def test_convert_rgba_png_with_transparency(self, temp_dir):
        """Тест конвертации PNG с прозрачностью."""
        # Создаем RGBA PNG с прозрачностью
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        png_path = temp_dir / "transparent.png"
        img.save(png_path, 'PNG')
        
        # Конвертируем
        jpeg_path = temp_dir / "converted.jpg"
        convert_png_to_jpeg(str(png_path), str(jpeg_path))
        
        # JPEG не поддерживает прозрачность, но конвертация должна пройти
        assert jpeg_path.exists()
        result_img = Image.open(jpeg_path)
        assert result_img.format == 'JPEG'
        assert result_img.mode == 'RGB'
    
    def test_convert_invalid_file(self, temp_dir):
        """Тест конвертации невалидного файла."""
        # Создаем текстовый файл вместо изображения
        invalid_path = temp_dir / "invalid.png"
        invalid_path.write_text("not an image")
        
        output_path = temp_dir / "output.jpg"
        
        # Должно выбросить исключение
        with pytest.raises(IconProcessingError):
            convert_png_to_jpeg(str(invalid_path), str(output_path))

