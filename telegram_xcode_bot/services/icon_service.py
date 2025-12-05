"""Сервис для работы с иконками приложения."""

import json
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from telegram_xcode_bot.logger import get_logger
from telegram_xcode_bot.exceptions import IconProcessingError

logger = get_logger(__name__)


def replace_app_icon(project_dir: str, new_icon_path: str) -> bool:
    """
    Заменяет иконку приложения в проекте.
    
    Ищет Assets.xcassets/AppIcon.appiconset и заменяет изображение 1024x1024.
    Обновляет Contents.json для правильной привязки иконки.
    
    Args:
        project_dir: Путь к директории проекта
        new_icon_path: Путь к новой иконке
    
    Returns:
        True если успешно заменено
        
    Raises:
        IconProcessingError: При ошибке обработки иконки
    """
    try:
        # Ищем Assets.xcassets/AppIcon.appiconset
        project_path = Path(project_dir)
        appiconset_paths = list(project_path.rglob('Assets.xcassets/AppIcon.appiconset'))
        
        if not appiconset_paths:
            logger.warning("Не найдена папка AppIcon.appiconset")
            return False
        
        icon_replaced = False
        for appiconset_path in appiconset_paths:
            # Читаем Contents.json
            contents_json_path = appiconset_path / 'Contents.json'
            
            if not contents_json_path.exists():
                logger.warning(f"Не найден Contents.json в {appiconset_path}")
                continue
            
            # Загружаем JSON
            with open(contents_json_path, 'r', encoding='utf-8') as f:
                contents = json.load(f)
            
            # Открываем новую иконку
            img = Image.open(new_icon_path)
            
            # Сначала собираем список старых файлов для удаления
            old_files_to_delete = []
            for image_entry in contents.get('images', []):
                size = image_entry.get('size')
                if size == '1024x1024':
                    old_filename = image_entry.get('filename')
                    if old_filename:
                        old_file_path = appiconset_path / old_filename
                        if old_file_path.exists():
                            old_files_to_delete.append(old_file_path)
            
            # Удаляем старые файлы
            for old_file in old_files_to_delete:
                try:
                    old_file.unlink()
                    logger.info(f"Удален старый файл иконки: {old_file.name}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить {old_file.name}: {e}")
            
            # Ищем все записи с размером 1024x1024 и обновляем их
            updated_count = 0
            for image_entry in contents.get('images', []):
                # Проверяем размер
                size = image_entry.get('size')
                if size == '1024x1024':
                    # Формируем имя файла на основе idiom и appearances
                    idiom = image_entry.get('idiom', 'universal')
                    scale = image_entry.get('scale', '1x')
                    
                    # Определяем имя файла
                    appearances = image_entry.get('appearances', [])
                    if appearances:
                        # Есть appearance (dark, tinted и т.д.)
                        appearance_value = appearances[0].get('value', 'any')
                        filename = f'AppIcon-{appearance_value}-1024.png'
                    else:
                        # Any appearance (по умолчанию)
                        filename = 'AppIcon-1024.png'
                    
                    # Обновляем filename в JSON
                    image_entry['filename'] = filename
                    
                    # Сохраняем иконку с нужным именем
                    target_icon = appiconset_path / filename
                    img.save(str(target_icon), 'PNG')
                    
                    logger.info(f"Создан файл иконки: {filename}")
                    updated_count += 1
            
            # Сохраняем обновленный Contents.json
            if updated_count > 0:
                with open(contents_json_path, 'w', encoding='utf-8') as f:
                    json.dump(contents, f, indent=2)
                
                logger.info(f"Обновлено {updated_count} иконок в {appiconset_path}")
                icon_replaced = True
            else:
                # Если не нашли записи 1024x1024, просто сохраняем как AppIcon-1024.png
                logger.warning(f"Не найдены записи 1024x1024 в Contents.json, сохраняем как AppIcon-1024.png")
                target_icon = appiconset_path / 'AppIcon-1024.png'
                img.save(str(target_icon), 'PNG')
                icon_replaced = True
        
        return icon_replaced
    except Exception as e:
        logger.error(f"Ошибка при замене иконки: {e}", exc_info=True)
        raise IconProcessingError(f"Не удалось заменить иконку: {str(e)}")


def convert_png_to_jpeg(image_path: str, output_path: str, quality: int = 95) -> None:
    """
    Конвертирует PNG в JPEG.
    
    Args:
        image_path: Путь к PNG изображению
        output_path: Путь для сохранения JPEG
        quality: Качество JPEG (0-100)
        
    Raises:
        IconProcessingError: При ошибке конвертации
    """
    try:
        img = Image.open(image_path)
        
        # Конвертируем PNG в RGB JPEG (без альфа-канала)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Создаем белый фон для прозрачных изображений
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        else:
            img = img.convert('RGB')
        
        # Сохраняем как JPEG
        img.save(output_path, 'JPEG', quality=quality)
        logger.info(f"PNG успешно конвертирован в JPEG: {output_path}")
    except Exception as e:
        logger.error(f"Ошибка при конвертации PNG в JPEG: {e}")
        raise IconProcessingError(f"Не удалось конвертировать изображение: {str(e)}")


def validate_icon(image_path: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет изображение на соответствие требованиям иконки.
    
    Args:
        image_path: Путь к изображению
    
    Returns:
        Tuple (валидность, сообщение об ошибке)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        img_format = img.format
        
        logger.info(f"Проверка изображения: формат={img_format}, размер={width}x{height}")
        
        # Проверяем формат
        if img_format not in ['JPEG', 'JPG', 'PNG']:
            return False, f"Неподдерживаемый формат: {img_format}. Требуется JPEG или PNG."
        
        # Проверяем размер
        if width != 1024 or height != 1024:
            return False, f"Неверный размер: {width}x{height}. Требуется 1024x1024."
        
        return True, None
    except Exception as e:
        logger.error(f"Ошибка при проверке изображения: {e}")
        return False, f"Не удалось прочитать изображение: {str(e)}"

