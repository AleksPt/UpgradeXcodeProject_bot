import os
import re
import zipfile
import tempfile
import shutil
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# КОНСТАНТЫ - ТЕКСТОВЫЕ СООБЩЕНИЯ
# ============================================================================

# Сообщения для пользователя
MSG_START_GREETING = (
    "Привет! 👋\n\n"
    "Отправьте мне архив с проектом Xcode (zip файл), "
    "и я увеличу версию и билд на 1, а затем верну обновленный архив."
)

MSG_WRONG_FILE_FORMAT = "❌ Пожалуйста, отправьте zip архив с проектом Xcode."

MSG_PROCESSING = "⏳ Обрабатываю архив..."

MSG_SUCCESS = "✅ Архив обновлен!\n\nТекущая версия: {}\nТекущий билд: {}"

MSG_ERROR_PREFIX = "❌ Произошла ошибка при обработке архива:\n"
MSG_ERROR_SUFFIX = (
    "\n\n"
    "Убедитесь, что архив содержит проект Xcode с файлами project.pbxproj"
)

# Сообщения об ошибках
ERROR_NO_PBXPROJ_FILES = "Не найдено файлов project.pbxproj в архиве"
ERROR_NO_FILES_UPDATED = "Не удалось обновить ни один файл project.pbxproj"

# Сообщения в логах
LOG_BOT_TOKEN_MISSING = "BOT_TOKEN не установлен! Установите переменную окружения BOT_TOKEN в Railway."
LOG_FILE_UPLOADED = "Загружен файл: {}"
LOG_FILE_UPDATED = "Обновлен файл: {}"
LOG_FILE_UPDATE_ERROR = "Ошибка при обновлении {}: {}"
LOG_FILES_PROCESSED = "Обработано файлов project.pbxproj: {}"
LOG_FILE_SENT = "Отправлен обновленный файл: {}"
LOG_ARCHIVE_ERROR = "Ошибка при обработке архива: {}"
LOG_BOT_STARTED = "Бот запущен..."

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

# Токен бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error(LOG_BOT_TOKEN_MISSING)
    raise ValueError(LOG_BOT_TOKEN_MISSING)


def increment_version(version_str):
    """Увеличивает версию на 1. Например: 1.0 -> 2.0, 1.2.3 -> 2.2.3"""
    parts = version_str.split('.')
    if parts:
        try:
            major = int(parts[0])
            major += 1
            parts[0] = str(major)
            return '.'.join(parts)
        except ValueError:
            return version_str
    return version_str


def increment_build_number(build_str):
    """Увеличивает build number на 1"""
    try:
        build_num = int(build_str)
        return str(build_num + 1)
    except ValueError:
        return build_str


def update_project_file(project_path):
    """Обновляет версию в project.pbxproj файле. Возвращает (успех, marketing_version, build_version)"""
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_marketing_version = None
        new_build_version = None
        
        # Обновляем MARKETING_VERSION (например, MARKETING_VERSION = 1.0;)
        marketing_pattern = r'(MARKETING_VERSION\s*=\s*)([^;]+)(;)'
        def replace_marketing(match):
            nonlocal new_marketing_version
            version = match.group(2).strip().strip('"')
            new_version = increment_version(version)
            new_marketing_version = new_version
            return f'{match.group(1)}{new_version}{match.group(3)}'
        content = re.sub(marketing_pattern, replace_marketing, content)
        
        # Обновляем CURRENT_PROJECT_VERSION (например, CURRENT_PROJECT_VERSION = 1;)
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
            logger.info(LOG_FILE_UPDATED.format(project_path))
            return (True, new_marketing_version, new_build_version)
        return (False, None, None)
    except Exception as e:
        logger.error(LOG_FILE_UPDATE_ERROR.format(project_path, e))
        return (False, None, None)


def process_archive(archive_path, output_path):
    """Обрабатывает архив: распаковывает, обновляет версии, запаковывает обратно.
    Возвращает (успех, marketing_version, build_version)"""
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем архив
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Ищем все project.pbxproj файлы
        project_files = list(Path(temp_dir).rglob('project.pbxproj'))
        
        if not project_files:
            raise ValueError(ERROR_NO_PBXPROJ_FILES)
        
        updated_count = 0
        marketing_version = None
        build_version = None
        
        for project_file in project_files:
            success, m_version, b_version = update_project_file(str(project_file))
            if success:
                updated_count += 1
                # Сохраняем версии из первого успешно обновленного файла
                if marketing_version is None:
                    marketing_version = m_version
                    build_version = b_version
        
        if updated_count == 0:
            raise ValueError(ERROR_NO_FILES_UPDATED)
        
        # Создаем новый архив
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zip_out.write(file_path, arc_name)
        
        logger.info(LOG_FILES_PROCESSED.format(updated_count))
        return (True, marketing_version, build_version)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(MSG_START_GREETING)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик документов (архивов)"""
    document = update.message.document
    
    # Проверяем, что это архив
    if not document.file_name or not document.file_name.lower().endswith(('.zip', '.zipx')):
        await update.message.reply_text(MSG_WRONG_FILE_FORMAT)
        return
    
    await update.message.reply_text(MSG_PROCESSING)
    
    try:
        # Скачиваем файл
        file = await context.bot.get_file(document.file_id)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        try:
            await file.download_to_drive(temp_input.name)
            logger.info(LOG_FILE_UPLOADED.format(document.file_name))
            
            # Обрабатываем архив
            success, marketing_version, build_version = process_archive(temp_input.name, temp_output.name)
            
            if not success:
                raise ValueError("Не удалось обработать архив")
            
            # Формируем сообщение с версиями
            success_message = MSG_SUCCESS.format(
                marketing_version or "неизвестно",
                build_version or "неизвестно"
            )
            
            # Отправляем обратно с фиксированным именем
            output_filename = "source.zip"
            
            await update.message.reply_document(
                document=open(temp_output.name, 'rb'),
                filename=output_filename,
                caption=success_message
            )
            logger.info(LOG_FILE_SENT.format(output_filename))
            
        finally:
            # Удаляем временные файлы
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            if os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
                
    except Exception as e:
        logger.error(LOG_ARCHIVE_ERROR.format(e), exc_info=True)
        await update.message.reply_text(
            MSG_ERROR_PREFIX + str(e) + MSG_ERROR_SUFFIX
        )


def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Запускаем бота
    logger.info(LOG_BOT_STARTED)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

