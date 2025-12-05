"""Обработчики callback запросов от inline кнопок."""

import os
import tempfile
import shutil
import zipfile
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram_xcode_bot.config import (
    MSG_WRONG_USER,
    MSG_FILE_NOT_FOUND,
    MSG_PROCESSING,
    MSG_WAITING_NAME,
    MSG_WAITING_BUNDLE_ID,
    MSG_WAITING_ICON,
    MSG_WAITING_DATE,
    MSG_DATE_NOT_FOUND,
    MSG_IPAD_ALREADY_SUPPORTED,
    MSG_RATE_LIMIT_EXCEEDED,
    MSG_ERROR_PREFIX,
    MSG_ERROR_SUFFIX,
    BUTTON_BACK,
    LOG_FILE_SENT,
    LOG_ARCHIVE_ERROR,
)
from telegram_xcode_bot.logger import get_logger
from telegram_xcode_bot.services.archive_service import process_archive_with_actions
from telegram_xcode_bot.services.xcode_service import read_project_info, find_activation_date_in_project, read_device_family
from telegram_xcode_bot.utils.rate_limiter import rate_limiter
from telegram_xcode_bot.utils.async_helpers import run_blocking_io
from telegram_xcode_bot.handlers.helpers import show_actions_menu

logger = get_logger(__name__)


async def increment_version_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Увеличить версию и билд'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Добавляем действие в список
    context.user_data[f'action_increment_version_{user_id}'] = True
    
    # Показываем обновленное меню
    await show_actions_menu(query, context, user_id, is_query=True)


async def change_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Изменить название'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Устанавливаем состояние ожидания ввода названия
    context.user_data[f'waiting_name_{user_id}'] = True
    
    # Создаем кнопку "Назад"
    keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(MSG_WAITING_NAME, reply_markup=reply_markup)


async def change_bundle_id_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Сменить Bundle ID'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[3])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Устанавливаем состояние ожидания ввода Bundle ID
    context.user_data[f'waiting_bundle_id_{user_id}'] = True
    
    # Создаем кнопку "Назад"
    keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(MSG_WAITING_BUNDLE_ID, reply_markup=reply_markup)


async def change_icon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Изменить иконку'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Устанавливаем состояние ожидания загрузки иконки
    context.user_data[f'waiting_icon_{user_id}'] = True
    
    # Создаем кнопку "Назад"
    keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(MSG_WAITING_ICON, reply_markup=reply_markup)


async def change_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Изменить дату активации'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Ищем дату активации в проекте
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем архив временно для поиска даты
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Ищем дату активации
        found, current_date, file_path, _ = find_activation_date_in_project(temp_dir)
        
        if not found:
            # Дата не найдена
            keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(MSG_DATE_NOT_FOUND, reply_markup=reply_markup)
            return
        
        # Дата найдена, показываем сообщение с текущей датой
        context.user_data[f'waiting_date_{user_id}'] = True
        
        keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"{MSG_WAITING_DATE}\n\n📌 Текущая дата: {current_date}"
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка при поиске даты активации: {e}", exc_info=True)
        keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("❌ Ошибка при чтении проекта", reply_markup=reply_markup)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def get_archive_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Получить обновлённый архив'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query or not query.message:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем rate limit для обработки архива
    if not rate_limiter.is_allowed(user_id):
        await query.answer(MSG_RATE_LIMIT_EXCEEDED, show_alert=True)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Собираем все действия
    actions = {
        'increment_version': context.user_data.get(f'action_increment_version_{user_id}', False),
        'new_name': context.user_data.get(f'action_new_name_{user_id}'),
        'new_bundle_id': context.user_data.get(f'action_new_bundle_id_{user_id}'),
        'new_icon_path': context.user_data.get(f'action_new_icon_{user_id}'),
        'new_activation_date': context.user_data.get(f'action_new_activation_date_{user_id}'),
        'add_ipad': context.user_data.get(f'action_add_ipad_{user_id}', False)
    }
    
    # Проверяем, есть ли хоть какие-то действия
    if not any([actions['increment_version'], actions['new_name'], actions['new_bundle_id'], 
                actions['new_icon_path'], actions['new_activation_date'], actions['add_ipad']]):
        await query.answer("Не выбрано ни одного действия!", show_alert=True)
        return
    
    # Обновляем сообщение - показываем процесс обработки
    await query.edit_message_text(MSG_PROCESSING)
    
    try:
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        try:
            # Обрабатываем архив со всеми действиями с тайм-аутом
            try:
                result = await run_blocking_io(
                    process_archive_with_actions,
                    archive_path,
                    temp_output.name,
                    actions
                )
            except TimeoutError as te:
                if os.path.exists(temp_output.name):
                    os.unlink(temp_output.name)
                await query.edit_message_text(
                    f"❌ {str(te)}\n\nАрхив слишком большой или операция занимает слишком много времени."
                )
                return
            
            if not result.success:
                raise ValueError(result.error_message or "Не удалось обработать архив")
            
            info = result.project_info
            
            # Определяем статус поддержки iPad
            ipad_status = "неизвестно"
            if result.device_family:
                if result.device_family == "Universal" or result.device_family == "iPad":
                    ipad_status = "поддерживается"
                elif result.device_family == "iPhone":
                    ipad_status = "не поддерживается"
            
            # Формируем сообщение с результатами
            success_message = (
                "✅ Архив обновлен!\n\n"
                f"Версия: {info.marketing_version or 'неизвестно'}\n"
                f"Билд: {info.build_version or 'неизвестно'}\n"
                f"Название: {info.display_name or 'неизвестно'}\n"
                f"Bundle ID: {info.bundle_id or 'неизвестно'}\n"
                f"Дата активации: {info.activation_date or 'не обнаружена'}\n"
                f"iPad: {ipad_status}"
            )
            
            # Отправляем обратно с фиксированным именем
            output_filename = "source.zip"
            
            with open(temp_output.name, 'rb') as output_file:
                await query.message.reply_document(
                    document=output_file,
                    filename=output_filename,
                    caption=success_message
                )
            logger.info(LOG_FILE_SENT.format(output_filename))
            
            # Удаляем временные файлы
            if os.path.exists(archive_path):
                os.unlink(archive_path)
            if os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
            
            # Очищаем user_data
            context.user_data.pop(f'archive_{user_id}', None)
            context.user_data.pop(f'file_name_{user_id}', None)
            context.user_data.pop(f'action_increment_version_{user_id}', None)
            context.user_data.pop(f'action_new_name_{user_id}', None)
            context.user_data.pop(f'action_new_bundle_id_{user_id}', None)
            context.user_data.pop(f'action_new_activation_date_{user_id}', None)
            context.user_data.pop(f'action_add_ipad_{user_id}', None)
            # Удаляем временный файл иконки
            icon_path = context.user_data.pop(f'action_new_icon_{user_id}', None)
            if icon_path and os.path.exists(icon_path):
                os.unlink(icon_path)
            
        except Exception as e:
            logger.error(LOG_ARCHIVE_ERROR.format(e), exc_info=True)
            await query.edit_message_text(MSG_ERROR_PREFIX + str(e) + MSG_ERROR_SUFFIX)
            # Удаляем временные файлы при ошибке
            if os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
                
    except Exception as e:
        logger.error(LOG_ARCHIVE_ERROR.format(e), exc_info=True)
        await query.edit_message_text(MSG_ERROR_PREFIX + str(e) + MSG_ERROR_SUFFIX)


async def project_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Информация о проекте'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Читаем информацию из архива
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем архив временно для чтения информации
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Ищем первый project.pbxproj файл
        project_files = list(Path(temp_dir).rglob('project.pbxproj'))
        
        if not project_files:
            await query.answer("Не найдено файлов project.pbxproj", show_alert=True)
            return
        
        # Читаем информацию из первого найденного файла
        info = read_project_info(str(project_files[0]))
        
        # Проверяем поддержку iPad
        device_family = read_device_family(str(project_files[0]))
        ipad_support = "неизвестно"
        if device_family == "Universal" or device_family == "iPad":
            ipad_support = "поддерживается"
        elif device_family == "iPhone":
            ipad_support = "не поддерживается"
        
        # Формируем сообщение с информацией
        info_message = (
            "ℹ️ Информация о проекте:\n\n"
            f"Версия: {info.marketing_version or 'неизвестно'}\n"
            f"Билд: {info.build_version or 'неизвестно'}\n"
            f"Название: {info.display_name or 'неизвестно'}\n"
            f"Bundle ID: {info.bundle_id or 'неизвестно'}\n"
            f"Дата активации: {info.activation_date or 'не обнаружена'}\n"
            f"iPad: {ipad_support}"
        )
        
        # Создаем кнопку "Назад"
        keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(info_message, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка при чтении информации о проекте: {e}", exc_info=True)
        await query.answer("Ошибка при чтении информации", show_alert=True)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Назад'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[1])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Убираем состояние ожидания ввода
    context.user_data.pop(f'waiting_name_{user_id}', None)
    context.user_data.pop(f'waiting_bundle_id_{user_id}', None)
    context.user_data.pop(f'waiting_icon_{user_id}', None)
    context.user_data.pop(f'waiting_date_{user_id}', None)
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Показываем меню действий
    await show_actions_menu(query, context, user_id, is_query=True)


async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Начать заново' - сбрасывает все действия.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[1])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Сбрасываем все действия
    context.user_data.pop(f'action_increment_version_{user_id}', None)
    context.user_data.pop(f'action_new_name_{user_id}', None)
    context.user_data.pop(f'action_new_bundle_id_{user_id}', None)
    context.user_data.pop(f'action_new_activation_date_{user_id}', None)
    context.user_data.pop(f'action_add_ipad_{user_id}', None)
    # Удаляем временный файл иконки если есть
    icon_path = context.user_data.pop(f'action_new_icon_{user_id}', None)
    if icon_path and os.path.exists(icon_path):
        os.unlink(icon_path)
    
    # Показываем меню заново
    await show_actions_menu(query, context, user_id, is_query=True)


async def add_ipad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатия на кнопку 'Добавить поддержку iPad'.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    # Извлекаем user_id из callback_data
    user_id = int(query.data.split('_')[2])
    
    # Проверяем, что это запрос от того же пользователя
    if query.from_user.id != user_id:
        await query.edit_message_text(MSG_WRONG_USER)
        return
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Проверяем текущее состояние поддержки устройств
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        project_files = list(Path(temp_dir).rglob('project.pbxproj'))
        if project_files:
            device_family = read_device_family(str(project_files[0]))
            if device_family == "Universal" or device_family == "iPad":
                # iPad уже поддерживается - показываем сообщение с кнопкой Назад
                await query.answer()
                keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(MSG_IPAD_ALREADY_SUPPORTED, reply_markup=reply_markup)
                return
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Добавляем действие в список
    context.user_data[f'action_add_ipad_{user_id}'] = True
    
    # Показываем обновленное меню
    await show_actions_menu(query, context, user_id, is_query=True)

