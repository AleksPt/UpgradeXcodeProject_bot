"""Обработчики документов и изображений."""

import os
import tempfile
import shutil
import zipfile
from pathlib import Path
from PIL import Image

from telegram import Update
from telegram.ext import ContextTypes

from telegram_xcode_bot.config import (
    MSG_WRONG_FILE_FORMAT,
    MSG_ICON_INVALID_FORMAT,
    LOG_FILE_UPLOADED,
    LOG_ARCHIVE_ERROR,
    MSG_ERROR_PREFIX,
    MSG_ERROR_SUFFIX,
)
from telegram_xcode_bot.logger import get_logger
from telegram_xcode_bot.services.xcode_service import read_project_info
from telegram_xcode_bot.services.icon_service import convert_png_to_jpeg
from telegram_xcode_bot.utils.validators import validate_icon_format, validate_icon_size
from telegram_xcode_bot.handlers.helpers import create_actions_keyboard

logger = get_logger(__name__)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик документов (архивов) - сохраняет файл и показывает кнопки.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    if not update.message or not update.message.document:
        return
    
    user_id = update.effective_user.id
    document = update.message.document
    
    # Если бот ждет иконку, передаем обработку в handle_photo_or_document
    if context.user_data.get(f'waiting_icon_{user_id}'):
        await handle_photo_or_document(update, context)
        return
    
    # Проверяем, что это архив
    if not document.file_name or not document.file_name.lower().endswith(('.zip', '.zipx')):
        await update.message.reply_text(MSG_WRONG_FILE_FORMAT)
        return
    
    try:
        # Скачиваем файл во временное хранилище
        file = await context.bot.get_file(document.file_id)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        await file.download_to_drive(temp_input.name)
        
        # Удаляем предыдущий архив если он есть
        old_archive = context.user_data.get(f'archive_{user_id}')
        if old_archive and os.path.exists(old_archive):
            os.unlink(old_archive)
            logger.info(f"Удален предыдущий архив: {old_archive}")
        
        # Удаляем старую иконку если она есть
        old_icon = context.user_data.get(f'action_new_icon_{user_id}')
        if old_icon and os.path.exists(old_icon):
            os.unlink(old_icon)
            logger.info(f"Удалена предыдущая иконка: {old_icon}")
        
        # Очищаем все действия при загрузке нового архива
        context.user_data.pop(f'action_increment_version_{user_id}', None)
        context.user_data.pop(f'action_new_name_{user_id}', None)
        context.user_data.pop(f'action_new_bundle_id_{user_id}', None)
        context.user_data.pop(f'action_new_icon_{user_id}', None)
        context.user_data.pop(f'action_new_activation_date_{user_id}', None)
        context.user_data.pop(f'waiting_name_{user_id}', None)
        context.user_data.pop(f'waiting_bundle_id_{user_id}', None)
        context.user_data.pop(f'waiting_icon_{user_id}', None)
        context.user_data.pop(f'waiting_date_{user_id}', None)
        
        context.user_data[f'archive_{user_id}'] = temp_input.name
        context.user_data[f'file_name_{user_id}'] = document.file_name
        
        logger.info(LOG_FILE_UPLOADED.format(document.file_name))
        
        # Читаем текущую информацию из архива
        temp_dir = tempfile.mkdtemp()
        try:
            # Распаковываем архив временно для чтения информации
            with zipfile.ZipFile(temp_input.name, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Ищем первый project.pbxproj файл
            project_files = list(Path(temp_dir).rglob('project.pbxproj'))
            
            marketing_version = "неизвестно"
            build_version = "неизвестно"
            display_name = "неизвестно"
            bundle_id = "неизвестно"
            activation_date = "не обнаружена"
            
            if project_files:
                # Читаем всю информацию из первого найденного файла
                info = read_project_info(str(project_files[0]))
                if info.marketing_version:
                    marketing_version = info.marketing_version
                if info.build_version:
                    build_version = info.build_version
                if info.display_name:
                    display_name = info.display_name
                if info.bundle_id:
                    bundle_id = info.bundle_id
                if info.activation_date:
                    activation_date = info.activation_date
        finally:
            # Удаляем временную директорию
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Создаем кнопки действий
        reply_markup = create_actions_keyboard(context.user_data, user_id)
        
        # Формируем сообщение с текущей информацией
        archive_message = (
            "📦 Архив получен!\n\n"
            f"Версия: {marketing_version}\n"
            f"Билд: {build_version}\n"
            f"Название: {display_name}\n"
            f"Bundle ID: {bundle_id}\n"
            f"Дата активации: {activation_date}\n\n"
            "Выбери действия:"
        )
        
        await update.message.reply_text(
            archive_message,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(LOG_ARCHIVE_ERROR.format(e), exc_info=True)
        await update.message.reply_text(
            MSG_ERROR_PREFIX + str(e) + MSG_ERROR_SUFFIX
        )


async def handle_photo_or_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик фотографий и документов - для загрузки иконки.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    if not update.message:
        return
    
    user_id = update.effective_user.id
    
    # Проверяем, ждет ли бот загрузки иконки
    if not context.user_data.get(f'waiting_icon_{user_id}'):
        return
    
    # Проверяем наличие архива
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        from telegram_xcode_bot.config import MSG_FILE_NOT_FOUND
        await update.message.reply_text(MSG_FILE_NOT_FOUND)
        context.user_data.pop(f'waiting_icon_{user_id}', None)
        return
    
    try:
        # Получаем файл (фото или документ)
        file_name = None
        if update.message.photo:
            # Берем фото наибольшего размера
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            file_name = "photo.jpg"
        elif update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
            file_name = update.message.document.file_name or "document"
            
            # Проверяем расширение файла
            if file_name:
                ext = file_name.lower().split('.')[-1]
                logger.info(f"Получен документ с расширением: {ext}")
                
                # Если это явно WebP или другой неподдерживаемый формат
                if ext in ['webp', 'svg', 'gif', 'bmp', 'tiff', 'tif', 'ico']:
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    from telegram_xcode_bot.config import BUTTON_BACK
                    keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"❌ Формат {ext.upper()} не поддерживается.\n\n"
                        f"Пожалуйста, отправь изображение в формате JPG или PNG, размером 1024x1024 пикселей.",
                        reply_markup=reply_markup
                    )
                    return
        else:
            return
        
        # Скачиваем файл
        temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        await file.download_to_drive(temp_image.name)
        logger.info(f"Файл скачан: {file_name}")
        
        # Проверяем изображение
        try:
            img = Image.open(temp_image.name)
            width, height = img.size
            img_format = img.format
            
            logger.info(f"Получено изображение: формат={img_format}, размер={width}x{height}, режим={img.mode}")
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            from telegram_xcode_bot.config import BUTTON_BACK, MSG_ICON_INVALID_SIZE
            
            # Проверяем формат
            if not validate_icon_format(img_format):
                keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    MSG_ICON_INVALID_FORMAT.format(img_format or "неизвестный"),
                    reply_markup=reply_markup
                )
                os.unlink(temp_image.name)
                return
            
            # Проверяем размер
            valid_size, error_msg = validate_icon_size(width, height)
            if not valid_size:
                keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    MSG_ICON_INVALID_SIZE.format(width, height),
                    reply_markup=reply_markup
                )
                os.unlink(temp_image.name)
                return
            
            # Конвертируем PNG в JPEG если нужно
            if img_format == 'PNG':
                logger.info(f"Конвертация PNG в JPEG для пользователя {user_id}")
                convert_png_to_jpeg(temp_image.name, temp_image.name, quality=95)
            
            # Все проверки пройдены
            context.user_data.pop(f'waiting_icon_{user_id}', None)
            context.user_data[f'action_new_icon_{user_id}'] = temp_image.name
            
            # Показываем обновленное меню
            from telegram_xcode_bot.handlers.helpers import show_actions_menu
            await show_actions_menu(update.message, context, user_id, is_query=False)
                
        except Exception as e:
            logger.error(f"Ошибка при проверке изображения: {e}", exc_info=True)
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            from telegram_xcode_bot.config import BUTTON_BACK
            keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                MSG_ICON_INVALID_FORMAT.format("неизвестный"),
                reply_markup=reply_markup
            )
            if os.path.exists(temp_image.name):
                os.unlink(temp_image.name)
                
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при обработке изображения")

