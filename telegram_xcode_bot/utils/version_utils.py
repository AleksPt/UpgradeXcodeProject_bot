"""Функции для работы с версиями и билдами."""

from typing import Optional, Tuple


def increment_version(version_str: str) -> str:
    """
    Увеличивает версию на 1.
    
    Примеры:
        1.0 -> 2.0
        1.2.3 -> 2.2.3
        5.1.2 -> 6.1.2
    
    Args:
        version_str: Строка с версией
    
    Returns:
        Увеличенная версия
    """
    parts = version_str.split('.')
    if parts:
        try:
            major = int(parts[0])
            major += 1
            parts[0] = str(major)
            return '.'.join(parts)
        except ValueError:
            return version_str
    return version_str


def increment_build_number(build_str: str) -> str:
    """
    Увеличивает build number на 1.
    
    Args:
        build_str: Строка с номером билда
    
    Returns:
        Увеличенный номер билда
    """
    try:
        build_num = int(build_str)
        return str(build_num + 1)
    except ValueError:
        return build_str


def parse_version(version_str: str) -> Optional[Tuple[int, ...]]:
    """
    Парсит версию в tuple чисел.
    
    Args:
        version_str: Строка с версией (например, "1.2.3")
    
    Returns:
        Tuple чисел (например, (1, 2, 3)) или None при ошибке
    """
    try:
        parts = version_str.split('.')
        return tuple(int(part) for part in parts)
    except (ValueError, AttributeError):
        return None

