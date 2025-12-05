"""Бизнес-логика для работы с Xcode проектами и архивами."""

from telegram_xcode_bot.services.xcode_service import (
    read_project_info,
    read_project_versions,
    update_project_file,
    update_display_name,
    update_bundle_id,
    find_activation_date_in_project,
    update_activation_date,
)
from telegram_xcode_bot.services.archive_service import (
    process_archive_with_actions,
    process_archive,
)
from telegram_xcode_bot.services.icon_service import replace_app_icon

__all__ = [
    "read_project_info",
    "read_project_versions",
    "update_project_file",
    "update_display_name",
    "update_bundle_id",
    "find_activation_date_in_project",
    "update_activation_date",
    "process_archive_with_actions",
    "process_archive",
    "replace_app_icon",
]

