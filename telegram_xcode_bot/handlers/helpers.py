"""Вспомогательные функции для handlers."""

from typing import Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram_xcode_bot.config import (
    BUTTON_INCREMENT_VERSION,
    BUTTON_CHANGE_NAME,
    BUTTON_CHANGE_BUNDLE_ID,
    BUTTON_CHANGE_ICON,
    BUTTON_CHANGE_DATE,
    BUTTON_ADD_IPAD,
    BUTTON_PROJECT_INFO,
    BUTTON_GET_ARCHIVE,
    BUTTON_RESET,
    MSG_VERSION_WILL_INCREMENT,
    MSG_NAME_WILL_CHANGE,
    MSG_BUNDLE_ID_WILL_CHANGE,
    MSG_ICON_WILL_CHANGE,
    MSG_DATE_WILL_CHANGE,
    MSG_IPAD_WILL_ADD,
)


def get_pending_actions_summary(user_data: Dict[str, Any], user_id: int) -> str:
    """
    Возвращает текст с описанием всех запланированных действий.
    
    Args:
        user_data: Данные пользователя из context
        user_id: ID пользователя
    
    Returns:
        Строка с описанием действий
    """
    actions = []
    
    if user_data.get(f'action_increment_version_{user_id}'):
        actions.append(MSG_VERSION_WILL_INCREMENT)
    
    new_name = user_data.get(f'action_new_name_{user_id}')
    if new_name:
        actions.append(MSG_NAME_WILL_CHANGE.format(new_name))
    
    new_bundle_id = user_data.get(f'action_new_bundle_id_{user_id}')
    if new_bundle_id:
        actions.append(MSG_BUNDLE_ID_WILL_CHANGE.format(new_bundle_id))
    
    new_icon_path = user_data.get(f'action_new_icon_{user_id}')
    if new_icon_path:
        actions.append(MSG_ICON_WILL_CHANGE)
    
    new_activation_date = user_data.get(f'action_new_activation_date_{user_id}')
    if new_activation_date:
        actions.append(MSG_DATE_WILL_CHANGE.format(new_activation_date))
    
    if user_data.get(f'action_add_ipad_{user_id}'):
        actions.append(MSG_IPAD_WILL_ADD)
    
    if not actions:
        return "Нет запланированных действий."
    
    return "Запланированные действия:\n" + "\n".join(actions)


def create_actions_keyboard(user_data: Dict[str, Any], user_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с действиями.
    
    Args:
        user_data: Данные пользователя из context
        user_id: ID пользователя
    
    Returns:
        InlineKeyboardMarkup с кнопками действий
    """
    keyboard = [
        [InlineKeyboardButton(BUTTON_INCREMENT_VERSION, callback_data=f"increment_version_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_NAME, callback_data=f"change_name_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_BUNDLE_ID, callback_data=f"change_bundle_id_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_ICON, callback_data=f"change_icon_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_DATE, callback_data=f"change_date_{user_id}")],
        [InlineKeyboardButton(BUTTON_ADD_IPAD, callback_data=f"add_ipad_{user_id}")],
        [InlineKeyboardButton(BUTTON_PROJECT_INFO, callback_data=f"project_info_{user_id}")]
    ]
    
    # Если есть хотя бы одно действие, добавляем кнопку получения архива
    if (user_data.get(f'action_increment_version_{user_id}') or 
        user_data.get(f'action_new_name_{user_id}') or 
        user_data.get(f'action_new_bundle_id_{user_id}') or
        user_data.get(f'action_new_icon_{user_id}') or
        user_data.get(f'action_new_activation_date_{user_id}') or
        user_data.get(f'action_add_ipad_{user_id}')):
        keyboard.append([InlineKeyboardButton(BUTTON_GET_ARCHIVE, callback_data=f"get_archive_{user_id}")])
        keyboard.append([InlineKeyboardButton(BUTTON_RESET, callback_data=f"reset_{user_id}")])
    
    return InlineKeyboardMarkup(keyboard)


async def show_actions_menu(
    query_or_message,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    is_query: bool = True
) -> None:
    """
    Показывает меню с доступными действиями и кнопкой получения архива.
    
    Args:
        query_or_message: CallbackQuery или Message объект
        context: Контекст обработчика
        user_id: ID пользователя
        is_query: True если это CallbackQuery, False если Message
    """
    # Получаем сводку запланированных действий
    actions_summary = get_pending_actions_summary(context.user_data, user_id)
    
    # Формируем текст сообщения
    message_text = f"📦 Архив загружен\n\n{actions_summary}\n\nВыбери действия:"
    
    # Создаем клавиатуру
    reply_markup = create_actions_keyboard(context.user_data, user_id)
    
    if is_query:
        await query_or_message.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await query_or_message.reply_text(message_text, reply_markup=reply_markup)

