"""Обработчики текстового ввода пользователей."""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram_xcode_bot.config import (
    MSG_FILE_NOT_FOUND,
    MSG_BUNDLE_ID_INVALID,
    MSG_DATE_INVALID,
    BUTTON_BACK,
)
from telegram_xcode_bot.logger import get_logger
from telegram_xcode_bot.utils.validators import validate_bundle_id, validate_date_format
from telegram_xcode_bot.handlers.helpers import show_actions_menu

logger = get_logger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик текстовых сообщений - для ввода нового названия, Bundle ID или даты активации.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    if not update.message:
        return
    
    user_id = update.effective_user.id
    
    # Проверяем, ждет ли бот ввода названия
    if context.user_data.get(f'waiting_name_{user_id}'):
        await handle_name_input(update, context, user_id)
        return
    
    # Проверяем, ждет ли бот ввода Bundle ID
    if context.user_data.get(f'waiting_bundle_id_{user_id}'):
        await handle_bundle_id_input(update, context, user_id)
        return
    
    # Проверяем, ждет ли бот ввода даты активации
    if context.user_data.get(f'waiting_date_{user_id}'):
        await handle_activation_date_input(update, context, user_id)
        return


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """
    Обработка ввода нового названия приложения.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
        user_id: ID пользователя
    """
    if not update.message:
        return
    
    # Проверяем наличие файла
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await update.message.reply_text(MSG_FILE_NOT_FOUND)
        context.user_data.pop(f'waiting_name_{user_id}', None)
        return
    
    # Получаем новое название
    new_name = update.message.text.strip()
    
    if not new_name:
        keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("❌ Название не может быть пустым. Попробуйте еще раз.", reply_markup=reply_markup)
        return
    
    # Убираем состояние ожидания
    context.user_data.pop(f'waiting_name_{user_id}', None)
    
    # Сохраняем новое название в действия
    context.user_data[f'action_new_name_{user_id}'] = new_name
    
    # Показываем обновленное меню
    await show_actions_menu(update.message, context, user_id, is_query=False)


async def handle_bundle_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """
    Обработка ввода нового Bundle ID.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
        user_id: ID пользователя
    """
    if not update.message:
        return
    
    # Проверяем наличие файла
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await update.message.reply_text(MSG_FILE_NOT_FOUND)
        context.user_data.pop(f'waiting_bundle_id_{user_id}', None)
        return
    
    # Получаем новый Bundle ID
    new_bundle_id = update.message.text.strip()
    
    # Проверяем валидность Bundle ID
    if not validate_bundle_id(new_bundle_id):
        keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MSG_BUNDLE_ID_INVALID, reply_markup=reply_markup)
        return
    
    # Убираем состояние ожидания
    context.user_data.pop(f'waiting_bundle_id_{user_id}', None)
    
    # Сохраняем новый Bundle ID в действия
    context.user_data[f'action_new_bundle_id_{user_id}'] = new_bundle_id
    
    # Показываем обновленное меню
    await show_actions_menu(update.message, context, user_id, is_query=False)


async def handle_activation_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """
    Обработка ввода новой даты активации.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
        user_id: ID пользователя
    """
    if not update.message:
        return
    
    # Проверяем наличие файла
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await update.message.reply_text(MSG_FILE_NOT_FOUND)
        context.user_data.pop(f'waiting_date_{user_id}', None)
        return
    
    # Получаем новую дату
    new_date = update.message.text.strip()
    
    # Проверяем валидность даты
    is_valid, error_message = validate_date_format(new_date)
    if not is_valid:
        keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MSG_DATE_INVALID.format(error_message), reply_markup=reply_markup)
        return
    
    # Убираем состояние ожидания
    context.user_data.pop(f'waiting_date_{user_id}', None)
    
    # Сохраняем новую дату в действия
    context.user_data[f'action_new_activation_date_{user_id}'] = new_date
    
    # Показываем обновленное меню
    await show_actions_menu(update.message, context, user_id, is_query=False)

