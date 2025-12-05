"""Точка входа для запуска через python -m telegram_xcode_bot."""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from telegram_xcode_bot.config import BOT_TOKEN, LOG_BOT_TOKEN_MISSING, LOG_BOT_STARTED
from telegram_xcode_bot.logger import logger
from telegram_xcode_bot.exceptions import ConfigurationError
from telegram_xcode_bot.handlers import (
    start_handler,
    handle_document,
    handle_photo_or_document,
    increment_version_callback,
    change_name_callback,
    change_bundle_id_callback,
    change_icon_callback,
    change_date_callback,
    add_ipad_callback,
    get_archive_callback,
    project_info_callback,
    back_callback,
    reset_callback,
    handle_text_message,
)


def main() -> None:
    """Запуск бота."""
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logger.error(LOG_BOT_TOKEN_MISSING)
        raise ConfigurationError(LOG_BOT_TOKEN_MISSING)
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_handler))
    
    # Регистрируем обработчики документов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Обработчик фото и документов с изображениями (для иконки)
    application.add_handler(
        MessageHandler(filters.PHOTO | (filters.Document.IMAGE), handle_photo_or_document)
    )
    
    # Обработчик текстовых сообщений (для ввода названия или Bundle ID)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Обработчики нажатий на кнопки
    application.add_handler(CallbackQueryHandler(increment_version_callback, pattern="^increment_version_"))
    application.add_handler(CallbackQueryHandler(change_name_callback, pattern="^change_name_"))
    application.add_handler(CallbackQueryHandler(change_bundle_id_callback, pattern="^change_bundle_id_"))
    application.add_handler(CallbackQueryHandler(change_icon_callback, pattern="^change_icon_"))
    application.add_handler(CallbackQueryHandler(change_date_callback, pattern="^change_date_"))
    application.add_handler(CallbackQueryHandler(add_ipad_callback, pattern="^add_ipad_"))
    application.add_handler(CallbackQueryHandler(project_info_callback, pattern="^project_info_"))
    application.add_handler(CallbackQueryHandler(get_archive_callback, pattern="^get_archive_"))
    application.add_handler(CallbackQueryHandler(reset_callback, pattern="^reset_"))
    application.add_handler(CallbackQueryHandler(back_callback, pattern="^back_"))
    
    # Запускаем бота
    logger.info(LOG_BOT_STARTED)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

