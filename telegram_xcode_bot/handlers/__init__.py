"""Telegram handlers для обработки сообщений и callback запросов."""

from telegram_xcode_bot.handlers.command_handlers import start_handler
from telegram_xcode_bot.handlers.document_handlers import (
    handle_document,
    handle_photo_or_document,
)
from telegram_xcode_bot.handlers.callback_handlers import (
    increment_version_callback,
    change_name_callback,
    change_bundle_id_callback,
    change_icon_callback,
    change_date_callback,
    get_archive_callback,
    project_info_callback,
    back_callback,
    reset_callback,
)
from telegram_xcode_bot.handlers.input_handlers import (
    handle_text_message,
    handle_name_input,
    handle_bundle_id_input,
    handle_activation_date_input,
)

__all__ = [
    "start_handler",
    "handle_document",
    "handle_photo_or_document",
    "increment_version_callback",
    "change_name_callback",
    "change_bundle_id_callback",
    "change_icon_callback",
    "change_date_callback",
    "get_archive_callback",
    "project_info_callback",
    "back_callback",
    "reset_callback",
    "handle_text_message",
    "handle_name_input",
    "handle_bundle_id_input",
    "handle_activation_date_input",
]

