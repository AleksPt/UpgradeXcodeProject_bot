"""Обработчики команд Telegram."""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_xcode_bot.config import MSG_START_GREETING
from telegram_xcode_bot.logger import get_logger

logger = get_logger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    
    Args:
        update: Telegram Update объект
        context: Контекст обработчика
    """
    if update.message:
        await update.message.reply_text(MSG_START_GREETING)
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")

