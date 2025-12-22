"""Сервис для работы с Xcode проектами."""

import re
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass

from telegram_xcode_bot.logger import get_logger
from telegram_xcode_bot.exceptions import XcodeProjectError
from telegram_xcode_bot.utils.version_utils import increment_version, increment_build_number

logger = get_logger(__name__)


@dataclass
class ProjectInfo:
    """Информация о Xcode проекте."""
    marketing_version: Optional[str] = None
    build_version: Optional[str] = None
    display_name: Optional[str] = None
    bundle_id: Optional[str] = None
    activation_date: Optional[str] = None


def read_project_versions(project_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Читает текущие версию и билд из project.pbxproj файла без изменения.
    
    Args:
        project_path: Путь к файлу project.pbxproj
    
    Returns:
        Tuple (marketing_version, build_version)
    """
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        marketing_version = None
        build_version = None
        
        # Ищем MARKETING_VERSION (например, MARKETING_VERSION = 1.0;)
        marketing_match = re.search(r'MARKETING_VERSION\s*=\s*([^;]+);', content)
        if marketing_match:
            marketing_version = marketing_match.group(1).strip().strip('"')
        
        # Ищем CURRENT_PROJECT_VERSION (например, CURRENT_PROJECT_VERSION = 1;)
        build_match = re.search(r'CURRENT_PROJECT_VERSION\s*=\s*([^;]+);', content)
        if build_match:
            build_version = build_match.group(1).strip().strip('"')
        
        return (marketing_version, build_version)
    except Exception as e:
        logger.error(f"Ошибка при чтении версий из {project_path}: {e}")
        return (None, None)


def read_project_info(project_path: str) -> ProjectInfo:
    """
    Читает всю информацию из project.pbxproj файла и ищет дату активации.
    
    Args:
        project_path: Путь к файлу project.pbxproj
    
    Returns:
        ProjectInfo с информацией о проекте
    """
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        info = ProjectInfo()
        
        # Ищем MARKETING_VERSION
        marketing_match = re.search(r'MARKETING_VERSION\s*=\s*([^;]+);', content)
        if marketing_match:
            info.marketing_version = marketing_match.group(1).strip().strip('"')
        
        # Ищем CURRENT_PROJECT_VERSION
        build_match = re.search(r'CURRENT_PROJECT_VERSION\s*=\s*([^;]+);', content)
        if build_match:
            info.build_version = build_match.group(1).strip().strip('"')
        
        # Ищем INFOPLIST_KEY_CFBundleDisplayName
        display_name_match = re.search(r'INFOPLIST_KEY_CFBundleDisplayName\s*=\s*([^;]+);', content)
        if display_name_match:
            info.display_name = display_name_match.group(1).strip().strip('"')
        
        # Ищем PRODUCT_BUNDLE_IDENTIFIER
        bundle_id_match = re.search(r'PRODUCT_BUNDLE_IDENTIFIER\s*=\s*([^;]+);', content)
        if bundle_id_match:
            info.bundle_id = bundle_id_match.group(1).strip().strip('"')
        
        # Ищем дату активации в проекте (возвращаемся к корневой директории проекта)
        project_dir = Path(project_path).parent.parent.parent
        found, activation_date, _, _ = find_activation_date_in_project(str(project_dir))
        if found:
            info.activation_date = activation_date
        
        return info
    except Exception as e:
        logger.error(f"Ошибка при чтении информации из {project_path}: {e}")
        return ProjectInfo()


def update_project_file(project_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Обновляет версию в project.pbxproj файле.
    
    Args:
        project_path: Путь к файлу project.pbxproj
    
    Returns:
        Tuple (успех, marketing_version, build_version)
    """
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_marketing_version = None
        new_build_version = None
        
        # Обновляем MARKETING_VERSION
        marketing_pattern = r'(MARKETING_VERSION\s*=\s*)([^;]+)(;)'
        def replace_marketing(match):
            nonlocal new_marketing_version
            version = match.group(2).strip().strip('"')
            new_version = increment_version(version)
            new_marketing_version = new_version
            return f'{match.group(1)}{new_version}{match.group(3)}'
        content = re.sub(marketing_pattern, replace_marketing, content)
        
        # Обновляем CURRENT_PROJECT_VERSION
        build_pattern = r'(CURRENT_PROJECT_VERSION\s*=\s*)([^;]+)(;)'
        def replace_build(match):
            nonlocal new_build_version
            build = match.group(2).strip().strip('"')
            new_build = increment_build_number(build)
            new_build_version = new_build
            return f'{match.group(1)}{new_build}{match.group(3)}'
        content = re.sub(build_pattern, replace_build, content)
        
        if content != original_content:
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Обновлен файл: {project_path}")
            return (True, new_marketing_version, new_build_version)
        return (False, None, None)
    except Exception as e:
        logger.error(f"Ошибка при обновлении {project_path}: {e}")
        return (False, None, None)


def update_display_name(project_path: str, new_name: str) -> bool:
    """
    Обновляет Display Name в project.pbxproj файле.
    
    Args:
        project_path: Путь к файлу project.pbxproj
        new_name: Новое название приложения
    
    Returns:
        True если успешно обновлено
    """
    try:
        # Обновляем project.pbxproj
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Экранируем кавычки в новом имени
        escaped_name = new_name.replace('"', '\\"')
        display_name_pattern = r'(INFOPLIST_KEY_CFBundleDisplayName\s*=\s*)([^;]+)(;)'
        
        def replace_display_name(match):
            return f'{match.group(1)}"{escaped_name}"{match.group(3)}'
        
        content = re.sub(display_name_pattern, replace_display_name, content)
        
        if content != original_content:
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Обновлено название в файле: {project_path}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении названия в {project_path}: {e}")
        return False


def update_bundle_id(project_path: str, new_bundle_id: str) -> bool:
    """
    Обновляет Product Bundle Identifier в project.pbxproj файле.
    
    Args:
        project_path: Путь к файлу project.pbxproj
        new_bundle_id: Новый Bundle ID
    
    Returns:
        True если успешно обновлено
    """
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        bundle_id_pattern = r'(PRODUCT_BUNDLE_IDENTIFIER\s*=\s*)([^;]+)(;)'
        
        def replace_bundle_id(match):
            return f'{match.group(1)}{new_bundle_id}{match.group(3)}'
        
        content = re.sub(bundle_id_pattern, replace_bundle_id, content)
        
        if content != original_content:
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Обновлен Bundle ID в файле: {project_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении Bundle ID в {project_path}: {e}")
        return False


def find_activation_date_in_project(
    project_dir: str
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Ищет .date(from: "...") во всех файлах .swift проекта.
    
    Args:
        project_dir: Путь к директории проекта
    
    Returns:
        Tuple (найдено, текущая_дата, путь_к_файлу, полное_совпадение)
    """
    try:
        project_path = Path(project_dir)
        swift_files = list(project_path.rglob('*.swift'))
        
        # Паттерн для поиска .date(from: "любые символы")
        date_pattern = r'\.date\(from:\s*"([^"]*)"\)'
        
        for swift_file in swift_files:
            try:
                with open(swift_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                match = re.search(date_pattern, content)
                if match:
                    current_date = match.group(1)
                    logger.info(f"Найдена дата активации '{current_date}' в файле: {swift_file}")
                    return (True, current_date, str(swift_file), match.group(0))
            except Exception as e:
                logger.warning(f"Ошибка при чтении файла {swift_file}: {e}")
                continue
        
        logger.info("Дата активации не найдена в проекте")
        return (False, None, None, None)
    except Exception as e:
        logger.error(f"Ошибка при поиске даты активации: {e}", exc_info=True)
        return (False, None, None, None)


def update_activation_date(project_dir: str, new_date: str) -> bool:
    """
    Обновляет дату активации в файлах .swift проекта.
    
    Args:
        project_dir: Путь к директории проекта
        new_date: Новая дата активации
    
    Returns:
        True если успешно обновлено
    """
    try:
        project_path = Path(project_dir)
        swift_files = list(project_path.rglob('*.swift'))
        
        # Паттерн для поиска и замены .date(from: "любые символы")
        date_pattern = r'(\.date\(from:\s*")([^"]*?)("\))'
        
        updated = False
        for swift_file in swift_files:
            try:
                with open(swift_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем, есть ли паттерн в файле
                if re.search(date_pattern, content):
                    # Заменяем дату
                    new_content = re.sub(date_pattern, rf'\g<1>{new_date}\g<3>', content)
                    
                    # Сохраняем файл
                    with open(swift_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    logger.info(f"Обновлена дата активации на '{new_date}' в файле: {swift_file}")
                    updated = True
            except Exception as e:
                logger.warning(f"Ошибка при обновлении файла {swift_file}: {e}")
                continue
        
        return updated
    except Exception as e:
        logger.error(f"Ошибка при обновлении даты активации: {e}", exc_info=True)
        return False


def read_device_family(project_path: str) -> Optional[str]:
    """
    Читает текущее значение TARGETED_DEVICE_FAMILY.
    
    Args:
        project_path: Путь к файлу project.pbxproj
    
    Returns:
        "iPhone" | "iPad" | "Universal" | None
    """
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.search(r'TARGETED_DEVICE_FAMILY\s*=\s*([^;]+);', content)
        if match:
            value = match.group(1).strip().strip('"')
            if value == "1":
                return "iPhone"
            elif value == "2":
                return "iPad"
            elif "1,2" in value or "2,1" in value:
                return "Universal"
        return None
    except Exception as e:
        logger.error(f"Ошибка при чтении TARGETED_DEVICE_FAMILY: {e}")
        return None


def add_ipad_support(project_path: str) -> bool:
    """
    Добавляет iPad в supported destinations.
    Изменяет TARGETED_DEVICE_FAMILY на "1,2" (Universal).
    
    Args:
        project_path: Путь к файлу project.pbxproj
    
    Returns:
        True если успешно обновлено
    """
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Паттерн для TARGETED_DEVICE_FAMILY
        device_family_pattern = r'(TARGETED_DEVICE_FAMILY\s*=\s*)([^;]+)(;)'
        
        def replace_device_family(match):
            current_value = match.group(2).strip().strip('"')
            # Если уже есть iPad (2 или 1,2), ничего не меняем
            if '2' in current_value:
                return match.group(0)
            # Добавляем iPad: 1 -> "1,2"
            return f'{match.group(1)}"1,2"{match.group(3)}'
        
        content = re.sub(device_family_pattern, replace_device_family, content)
        
        if content != original_content:
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Добавлена поддержка iPad в файле: {project_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при добавлении поддержки iPad в {project_path}: {e}")
        return False

