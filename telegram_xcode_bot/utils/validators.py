"""Функции валидации данных."""

import re
from typing import Tuple, Optional


def validate_bundle_id(bundle_id: str) -> bool:
    """
    Проверяет корректность Bundle ID.
    
    Правила:
    - Только латинские буквы, цифры, дефисы и точки
    - Первый символ должен быть буквой
    - Без пробелов
    
    Args:
        bundle_id: Bundle ID для проверки
    
    Returns:
        True если валидный, False если нет
    """
    if not bundle_id:
        return False
    
    # Проверка первого символа - должна быть буква
    if not bundle_id[0].isalpha():
        return False
    
    # Проверка всех символов - только буквы, цифры, дефисы и точки
    pattern = r'^[a-zA-Z][a-zA-Z0-9.-]*$'
    return bool(re.match(pattern, bundle_id))


def validate_icon_format(img_format: Optional[str]) -> bool:
    """
    Проверяет, что формат изображения поддерживается.
    
    Args:
        img_format: Формат изображения (например, 'JPEG', 'PNG')
    
    Returns:
        True если формат поддерживается
    """
    if not img_format:
        return False
    return img_format.upper() in ['JPEG', 'JPG', 'PNG']


def validate_icon_size(width: int, height: int) -> Tuple[bool, Optional[str]]:
    """
    Проверяет размер иконки.
    
    Args:
        width: Ширина изображения
        height: Высота изображения
    
    Returns:
        Tuple (валидность, сообщение об ошибке)
    """
    required_size = 1024
    if width == required_size and height == required_size:
        return True, None
    return False, f"Текущий размер: {width}x{height}, требуемый: {required_size}x{required_size}"


def validate_date_format(date_str: str) -> bool:
    """
    Проверяет формат даты (год/месяц/день).
    
    Args:
        date_str: Строка с датой
    
    Returns:
        True если формат корректен
    """
    if not date_str:
        return False
    
    # Проверяем формат YYYY/MM/DD
    pattern = r'^\d{4}/\d{2}/\d{2}$'
    return bool(re.match(pattern, date_str))

