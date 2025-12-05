"""Сервис для работы с архивами проектов."""

import os
import tempfile
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from telegram_xcode_bot.logger import get_logger
from telegram_xcode_bot.exceptions import ArchiveProcessingError
from telegram_xcode_bot.config import ERROR_NO_PBXPROJ_FILES, ERROR_NO_FILES_UPDATED
from telegram_xcode_bot.services.xcode_service import (
    update_project_file,
    update_display_name,
    update_bundle_id,
    read_project_info,
    ProjectInfo,
    update_activation_date,
    add_ipad_support,
)
from telegram_xcode_bot.services.icon_service import replace_app_icon

logger = get_logger(__name__)


@dataclass
class ArchiveProcessResult:
    """Результат обработки архива."""
    success: bool
    project_info: ProjectInfo
    error_message: Optional[str] = None


def extract_archive(archive_path: str, extract_dir: str) -> None:
    """
    Распаковывает архив в указанную директорию.
    
    Args:
        archive_path: Путь к архиву
        extract_dir: Директория для распаковки
        
    Raises:
        ArchiveProcessingError: При ошибке распаковки
    """
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        logger.info(f"Архив распакован в {extract_dir}")
    except Exception as e:
        logger.error(f"Ошибка при распаковке архива: {e}")
        raise ArchiveProcessingError(f"Не удалось распаковать архив: {str(e)}")


def create_archive(source_dir: str, output_path: str) -> None:
    """
    Создает zip архив из указанной директории.
    
    Args:
        source_dir: Директория с файлами
        output_path: Путь для создания архива
        
    Raises:
        ArchiveProcessingError: При ошибке создания архива
    """
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, source_dir)
                    zip_out.write(file_path, arc_name)
        logger.info(f"Создан архив: {output_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании архива: {e}")
        raise ArchiveProcessingError(f"Не удалось создать архив: {str(e)}")


def process_archive_with_actions(
    archive_path: str,
    output_path: str,
    actions: Dict[str, Any]
) -> ArchiveProcessResult:
    """
    Обрабатывает архив, применяя все запланированные действия.
    
    Args:
        archive_path: Путь к исходному архиву
        output_path: Путь для сохранения обработанного архива
        actions: Словарь с ключами:
            - increment_version: bool
            - new_name: str | None
            - new_bundle_id: str | None
            - new_icon_path: str | None
            - new_activation_date: str | None
            - add_ipad: bool
    
    Returns:
        ArchiveProcessResult с результатом обработки
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем архив
        extract_archive(archive_path, temp_dir)
        
        # Ищем все project.pbxproj файлы
        project_files = list(Path(temp_dir).rglob('project.pbxproj'))
        
        if not project_files:
            raise ArchiveProcessingError(ERROR_NO_PBXPROJ_FILES)
        
        project_info = ProjectInfo()
        
        # Применяем все действия к каждому файлу
        for project_file in project_files:
            project_path = str(project_file)
            
            # Увеличиваем версию если нужно
            if actions.get('increment_version'):
                success, m_version, b_version = update_project_file(project_path)
                if success and project_info.marketing_version is None:
                    project_info.marketing_version = m_version
                    project_info.build_version = b_version
            
            # Меняем название если указано
            if actions.get('new_name'):
                update_display_name(project_path, actions['new_name'])
            
            # Меняем Bundle ID если указан
            if actions.get('new_bundle_id'):
                update_bundle_id(project_path, actions['new_bundle_id'])
            
            # Добавляем поддержку iPad если указано
            if actions.get('add_ipad'):
                add_ipad_support(project_path)
        
        # Меняем иконку если указана
        if actions.get('new_icon_path'):
            replace_app_icon(temp_dir, actions['new_icon_path'])
        
        # Меняем дату активации если указана
        if actions.get('new_activation_date'):
            update_activation_date(temp_dir, actions['new_activation_date'])
        
        # Читаем финальную информацию из обработанного файла
        if project_files:
            project_info = read_project_info(str(project_files[0]))
        
        # Создаем новый архив
        create_archive(temp_dir, output_path)
        
        logger.info(f"Обработан архив с действиями: {actions}")
        return ArchiveProcessResult(success=True, project_info=project_info)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке архива: {e}", exc_info=True)
        return ArchiveProcessResult(
            success=False,
            project_info=ProjectInfo(),
            error_message=str(e)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def process_archive(archive_path: str, output_path: str) -> ArchiveProcessResult:
    """
    Обрабатывает архив: распаковывает, обновляет версии, запаковывает обратно.
    
    Args:
        archive_path: Путь к исходному архиву
        output_path: Путь для сохранения обработанного архива
    
    Returns:
        ArchiveProcessResult с результатом обработки
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем архив
        extract_archive(archive_path, temp_dir)
        
        # Ищем все project.pbxproj файлы
        project_files = list(Path(temp_dir).rglob('project.pbxproj'))
        
        if not project_files:
            raise ArchiveProcessingError(ERROR_NO_PBXPROJ_FILES)
        
        updated_count = 0
        project_info = ProjectInfo()
        
        for project_file in project_files:
            success, m_version, b_version = update_project_file(str(project_file))
            if success:
                updated_count += 1
                # Сохраняем версии из первого успешно обновленного файла
                if project_info.marketing_version is None:
                    project_info.marketing_version = m_version
                    project_info.build_version = b_version
        
        if updated_count == 0:
            raise ArchiveProcessingError(ERROR_NO_FILES_UPDATED)
        
        # Создаем новый архив
        create_archive(temp_dir, output_path)
        
        logger.info(f"Обработано файлов project.pbxproj: {updated_count}")
        return ArchiveProcessResult(success=True, project_info=project_info)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке архива: {e}", exc_info=True)
        return ArchiveProcessResult(
            success=False,
            project_info=ProjectInfo(),
            error_message=str(e)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

