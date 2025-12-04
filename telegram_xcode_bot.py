import os
import re
import zipfile
import tempfile
import shutil
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import logging
from PIL import Image

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
    "Я могу увеличить версию + билд в проекте Xcode, изменить название приложения и Bundle ID.\n"
    "Пришли мне архив с проектом (zip файл)."
)

MSG_WRONG_FILE_FORMAT = "❌ Пожалуйста, отправь zip архив с проектом Xcode."

MSG_PROCESSING = "⏳ Обрабатываю архив..."

MSG_SUCCESS = "✅ Архив обновлен!\n\nНовая версия: {}\nНовый билд: {}"

MSG_ACTION_ADDED = "✅ Действие добавлено!\n\n{}\n\nВыбери ещё действия или получи обновлённый архив."

MSG_VERSION_WILL_INCREMENT = "🆙 Версия и билд будут увеличены"
MSG_NAME_WILL_CHANGE = "✏️ Название изменится на: {}"
MSG_BUNDLE_ID_WILL_CHANGE = "📦 Bundle ID изменится на: {}"
MSG_ICON_WILL_CHANGE = "🎨 Иконка будет изменена"

MSG_WAITING_NAME = "✏️ Введи новое название приложения:"

MSG_NAME_CHANGED = "✅ Название успешно изменено на: {}"

MSG_WAITING_BUNDLE_ID = (
    "📦 Введи новый Bundle ID:\n\n"
    "Требования:\n"
    "• Только латинские буквы, цифры, дефисы и точки\n"
    "• Первый символ должен быть буквой\n"
    "• Без пробелов\n\n"
    "Пример: com.example.myapp"
)

MSG_WAITING_ICON = (
    "🎨 Отправь новую иконку приложения:\n\n"
    "Требования:\n"
    "• Формат: JPG или PNG\n"
    "• Размер: 1024x1024 пикселей\n\n"
    "Отправь файл или изображение.\n"
    "PNG будет автоматически конвертирован в JPG."
)

MSG_ICON_INVALID_FORMAT = (
    "❌ Неверный формат изображения!\n\n"
    "Текущий формат: {}\n"
    "Поддерживаемые форматы: JPG, PNG\n"
    "Размер: 1024x1024 пикселей\n\n"
    "Попробуй еще раз."
)

MSG_ICON_INVALID_SIZE = (
    "❌ Неверный размер изображения!\n\n"
    "Текущий размер: {}x{}\n"
    "Требуемый размер: 1024x1024 пикселей\n\n"
    "Попробуй еще раз."
)

MSG_BUNDLE_ID_INVALID = (
    "❌ Неверный формат Bundle ID!\n\n"
    "Требования:\n"
    "• Только латинские буквы, цифры, дефисы и точки\n"
    "• Первый символ должен быть буквой\n"
    "• Без пробелов\n\n"
    "Попробуй еще раз."
)

MSG_WRONG_USER = "❌ Ты не можешь обработать чужой архив."

MSG_FILE_NOT_FOUND = "❌ Файл не найден. Пожалуйста, отправь архив заново."

# Тексты кнопок
BUTTON_INCREMENT_VERSION = "🆙 Увеличить версию и билд"
BUTTON_CHANGE_NAME = "✏️ Изменить название"
BUTTON_CHANGE_BUNDLE_ID = "📦 Сменить Bundle ID"
BUTTON_CHANGE_ICON = "🎨 Изменить иконку"
BUTTON_PROJECT_INFO = "ℹ️ Информация о проекте"
BUTTON_GET_ARCHIVE = "📥 Получить обновлённый архив"
BUTTON_BACK = "⬅️ Назад"
BUTTON_RESET = "🔄 Начать заново"

MSG_ERROR_PREFIX = "❌ Произошла ошибка при обработке архива:\n"
MSG_ERROR_SUFFIX = (
    "\n\n"
    "Убедись, что архив содержит проект Xcode с файлами project.pbxproj"
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


def get_pending_actions_summary(user_data, user_id):
    """Возвращает текст с описанием всех запланированных действий"""
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
    
    if not actions:
        return "Нет запланированных действий."
    
    return "Запланированные действия:\n" + "\n".join(actions)


def validate_bundle_id(bundle_id):
    """Проверяет корректность Bundle ID.
    Правила:
    - Только латинские буквы, цифры, дефисы и точки
    - Первый символ должен быть буквой
    - Без пробелов
    Возвращает True если валидный, False если нет"""
    if not bundle_id:
        return False
    
    # Проверка первого символа - должна быть буква
    if not bundle_id[0].isalpha():
        return False
    
    # Проверка всех символов - только буквы, цифры, дефисы и точки
    pattern = r'^[a-zA-Z][a-zA-Z0-9.-]*$'
    return bool(re.match(pattern, bundle_id))


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


def read_project_versions(project_path):
    """Читает текущие версию и билд из project.pbxproj файла без изменения.
    Возвращает (marketing_version, build_version)"""
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        marketing_version = None
        build_version = None
        
        # Ищем MARKETING_VERSION (например, MARKETING_VERSION = 1.0;)
        marketing_match = re.search(r'MARKETING_VERSION\s*=\s*([^;]+);', content)
        if marketing_match:
            marketing_version = marketing_match.group(1).strip().strip('"')
        
        # Ищем CURRENT_PROJECT_VERSION (например, CURRENT_PROJECT_VERSION = 1;)
        build_match = re.search(r'CURRENT_PROJECT_VERSION\s*=\s*([^;]+);', content)
        if build_match:
            build_version = build_match.group(1).strip().strip('"')
        
        return (marketing_version, build_version)
    except Exception as e:
        logger.error(f"Ошибка при чтении версий из {project_path}: {e}")
        return (None, None)


def read_project_info(project_path):
    """Читает всю информацию из project.pbxproj файла.
    Возвращает (marketing_version, build_version, display_name, bundle_id)"""
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        marketing_version = None
        build_version = None
        display_name = None
        bundle_id = None
        
        # Ищем MARKETING_VERSION
        marketing_match = re.search(r'MARKETING_VERSION\s*=\s*([^;]+);', content)
        if marketing_match:
            marketing_version = marketing_match.group(1).strip().strip('"')
        
        # Ищем CURRENT_PROJECT_VERSION
        build_match = re.search(r'CURRENT_PROJECT_VERSION\s*=\s*([^;]+);', content)
        if build_match:
            build_version = build_match.group(1).strip().strip('"')
        
        # Ищем INFOPLIST_KEY_CFBundleDisplayName
        display_name_match = re.search(r'INFOPLIST_KEY_CFBundleDisplayName\s*=\s*([^;]+);', content)
        if display_name_match:
            display_name = display_name_match.group(1).strip().strip('"')
        
        # Ищем PRODUCT_BUNDLE_IDENTIFIER
        bundle_id_match = re.search(r'PRODUCT_BUNDLE_IDENTIFIER\s*=\s*([^;]+);', content)
        if bundle_id_match:
            bundle_id = bundle_id_match.group(1).strip().strip('"')
        
        return (marketing_version, build_version, display_name, bundle_id)
    except Exception as e:
        logger.error(f"Ошибка при чтении информации из {project_path}: {e}")
        return (None, None, None, None)


def update_display_name(project_path, new_name):
    """Обновляет Display Name в project.pbxproj файле.
    Возвращает True если успешно обновлено"""
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Обновляем INFOPLIST_KEY_CFBundleDisplayName (например, INFOPLIST_KEY_CFBundleDisplayName = "Old Name";)
        # Экранируем кавычки в новом имени
        escaped_name = new_name.replace('"', '\\"')
        display_name_pattern = r'(INFOPLIST_KEY_CFBundleDisplayName\s*=\s*)([^;]+)(;)'
        
        def replace_display_name(match):
            return f'{match.group(1)}"{escaped_name}"{match.group(3)}'
        
        content = re.sub(display_name_pattern, replace_display_name, content)
        
        if content != original_content:
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Обновлено название в файле: {project_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении названия в {project_path}: {e}")
        return False


def update_bundle_id(project_path, new_bundle_id):
    """Обновляет Product Bundle Identifier в project.pbxproj файле.
    Возвращает True если успешно обновлено"""
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Обновляем PRODUCT_BUNDLE_IDENTIFIER (например, PRODUCT_BUNDLE_IDENTIFIER = com.example.myapp;)
        bundle_id_pattern = r'(PRODUCT_BUNDLE_IDENTIFIER\s*=\s*)([^;]+)(;)'
        
        def replace_bundle_id(match):
            return f'{match.group(1)}{new_bundle_id}{match.group(3)}'
        
        content = re.sub(bundle_id_pattern, replace_bundle_id, content)
        
        if content != original_content:
            with open(project_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Обновлен Bundle ID в файле: {project_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении Bundle ID в {project_path}: {e}")
        return False


def replace_app_icon(project_dir, new_icon_path):
    """Заменяет иконку приложения в проекте.
    Ищет Assets.xcassets/AppIcon.appiconset и заменяет изображение 1024x1024.
    Возвращает True если успешно заменено"""
    try:
        # Ищем Assets.xcassets/AppIcon.appiconset
        project_path = Path(project_dir)
        appiconset_paths = list(project_path.rglob('Assets.xcassets/AppIcon.appiconset'))
        
        if not appiconset_paths:
            logger.warning("Не найдена папка AppIcon.appiconset")
            return False
        
        icon_replaced = False
        for appiconset_path in appiconset_paths:
            # Копируем новую иконку как AppIcon-1024.png (стандартное имя для 1024x1024)
            target_icon = appiconset_path / 'AppIcon-1024.png'
            
            # Конвертируем в PNG если нужно
            img = Image.open(new_icon_path)
            img.save(str(target_icon), 'PNG')
            
            logger.info(f"Заменена иконка в {appiconset_path}")
            icon_replaced = True
        
        return icon_replaced
    except Exception as e:
        logger.error(f"Ошибка при замене иконки: {e}")
        return False




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


def process_archive_with_actions(archive_path, output_path, actions):
    """Обрабатывает архив применяя все запланированные действия.
    actions - словарь с ключами: increment_version, new_name, new_bundle_id, new_icon_path
    Возвращает (успех, marketing_version, build_version, display_name, bundle_id)"""
    temp_dir = tempfile.mkdtemp()
    try:
        # Распаковываем архив
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Ищем все project.pbxproj файлы
        project_files = list(Path(temp_dir).rglob('project.pbxproj'))
        
        if not project_files:
            raise ValueError(ERROR_NO_PBXPROJ_FILES)
        
        marketing_version = None
        build_version = None
        display_name = None
        bundle_id = None
        
        # Применяем все действия к каждому файлу
        for project_file in project_files:
            project_path = str(project_file)
            
            # Увеличиваем версию если нужно
            if actions.get('increment_version'):
                success, m_version, b_version = update_project_file(project_path)
                if success and marketing_version is None:
                    marketing_version = m_version
                    build_version = b_version
            
            # Меняем название если указано
            if actions.get('new_name'):
                update_display_name(project_path, actions['new_name'])
            
            # Меняем Bundle ID если указан
            if actions.get('new_bundle_id'):
                update_bundle_id(project_path, actions['new_bundle_id'])
        
        # Меняем иконку если указана
        if actions.get('new_icon_path'):
            replace_app_icon(temp_dir, actions['new_icon_path'])
        
        # Читаем финальную информацию из обработанного файла
        if project_files:
            marketing_version, build_version, display_name, bundle_id = read_project_info(str(project_files[0]))
        
        # Создаем новый архив
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zip_out.write(file_path, arc_name)
        
        logger.info(f"Обработан архив с действиями: {actions}")
        return (True, marketing_version, build_version, display_name, bundle_id)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


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
    """Обработчик документов (архивов) - сохраняет файл и показывает кнопку"""
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
        
        # Сохраняем путь к файлу в user_data для последующей обработки
        user_id = update.effective_user.id
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
            
            if project_files:
                # Читаем всю информацию из первого найденного файла
                m_version, b_version, d_name, b_id = read_project_info(str(project_files[0]))
                if m_version:
                    marketing_version = m_version
                if b_version:
                    build_version = b_version
                if d_name:
                    display_name = d_name
                if b_id:
                    bundle_id = b_id
        finally:
            # Удаляем временную директорию
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Создаем кнопки действий
        keyboard = [
            [InlineKeyboardButton(BUTTON_INCREMENT_VERSION, callback_data=f"increment_version_{user_id}")],
            [InlineKeyboardButton(BUTTON_CHANGE_NAME, callback_data=f"change_name_{user_id}")],
            [InlineKeyboardButton(BUTTON_CHANGE_BUNDLE_ID, callback_data=f"change_bundle_id_{user_id}")],
            [InlineKeyboardButton(BUTTON_CHANGE_ICON, callback_data=f"change_icon_{user_id}")],
            [InlineKeyboardButton(BUTTON_PROJECT_INFO, callback_data=f"project_info_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Формируем сообщение с текущей информацией
        archive_message = (
            "📦 Архив получен!\n\n"
            f"Версия: {marketing_version}\n"
            f"Билд: {build_version}\n"
            f"Название: {display_name}\n"
            f"Bundle ID: {bundle_id}\n\n"
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


async def show_actions_menu(query_or_message, context: ContextTypes.DEFAULT_TYPE, user_id: int, is_query: bool = True):
    """Показывает меню с доступными действиями и кнопкой получения архива"""
    # Получаем сводку запланированных действий
    actions_summary = get_pending_actions_summary(context.user_data, user_id)
    
    # Формируем текст сообщения
    message_text = f"📦 Архив загружен\n\n{actions_summary}\n\nВыбери действия:"
    
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton(BUTTON_INCREMENT_VERSION, callback_data=f"increment_version_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_NAME, callback_data=f"change_name_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_BUNDLE_ID, callback_data=f"change_bundle_id_{user_id}")],
        [InlineKeyboardButton(BUTTON_CHANGE_ICON, callback_data=f"change_icon_{user_id}")],
        [InlineKeyboardButton(BUTTON_PROJECT_INFO, callback_data=f"project_info_{user_id}")]
    ]
    
    # Если есть хотя бы одно действие, добавляем кнопку получения архива
    if (context.user_data.get(f'action_increment_version_{user_id}') or 
        context.user_data.get(f'action_new_name_{user_id}') or 
        context.user_data.get(f'action_new_bundle_id_{user_id}') or
        context.user_data.get(f'action_new_icon_{user_id}')):
        keyboard.append([InlineKeyboardButton(BUTTON_GET_ARCHIVE, callback_data=f"get_archive_{user_id}")])
        keyboard.append([InlineKeyboardButton(BUTTON_RESET, callback_data=f"reset_{user_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_query:
        await query_or_message.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await query_or_message.reply_text(message_text, reply_markup=reply_markup)


async def increment_version_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Увеличить версию и билд'"""
    query = update.callback_query
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


async def get_archive_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Получить обновлённый архив'"""
    query = update.callback_query
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
    
    # Собираем все действия
    actions = {
        'increment_version': context.user_data.get(f'action_increment_version_{user_id}', False),
        'new_name': context.user_data.get(f'action_new_name_{user_id}'),
        'new_bundle_id': context.user_data.get(f'action_new_bundle_id_{user_id}'),
        'new_icon_path': context.user_data.get(f'action_new_icon_{user_id}')
    }
    
    # Проверяем, есть ли хоть какие-то действия
    if not any([actions['increment_version'], actions['new_name'], actions['new_bundle_id'], actions['new_icon_path']]):
        await query.answer("Не выбрано ни одного действия!", show_alert=True)
        return
    
    # Обновляем сообщение - показываем процесс обработки
    await query.edit_message_text(MSG_PROCESSING)
    
    try:
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        try:
            # Обрабатываем архив со всеми действиями
            success, marketing_version, build_version, display_name, bundle_id = process_archive_with_actions(
                archive_path, temp_output.name, actions
            )
            
            if not success:
                raise ValueError("Не удалось обработать архив")
            
            # Формируем сообщение с результатами (всегда показываем все параметры)
            success_message = (
                "✅ Архив обновлен!\n\n"
                f"Версия: {marketing_version or 'неизвестно'}\n"
                f"Билд: {build_version or 'неизвестно'}\n"
                f"Название: {display_name or 'неизвестно'}\n"
                f"Bundle ID: {bundle_id or 'неизвестно'}"
            )
            
            # Отправляем обратно с фиксированным именем
            output_filename = "source.zip"
            
            await query.message.reply_document(
                document=open(temp_output.name, 'rb'),
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
            # Удаляем временный файл иконки
            icon_path = context.user_data.pop(f'action_new_icon_{user_id}', None)
            if icon_path and os.path.exists(icon_path):
                os.unlink(icon_path)
            
        except Exception as e:
            logger.error(LOG_ARCHIVE_ERROR.format(e), exc_info=True)
            await query.edit_message_text(
                MSG_ERROR_PREFIX + str(e) + MSG_ERROR_SUFFIX
            )
            # Удаляем временные файлы при ошибке
            if os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
                
    except Exception as e:
        logger.error(LOG_ARCHIVE_ERROR.format(e), exc_info=True)
        await query.edit_message_text(
            MSG_ERROR_PREFIX + str(e) + MSG_ERROR_SUFFIX
        )


async def project_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Информация о проекте'"""
    query = update.callback_query
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
        marketing_version, build_version, display_name, bundle_id = read_project_info(str(project_files[0]))
        
        # Формируем сообщение с информацией
        info_message = (
            "ℹ️ Информация о проекте:\n\n"
            f"Версия: {marketing_version or 'неизвестно'}\n"
            f"Билд: {build_version or 'неизвестно'}\n"
            f"Название: {display_name or 'неизвестно'}\n"
            f"Bundle ID: {bundle_id or 'неизвестно'}"
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


async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Начать заново' - сбрасывает все действия"""
    query = update.callback_query
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
    # Удаляем временный файл иконки если есть
    icon_path = context.user_data.pop(f'action_new_icon_{user_id}', None)
    if icon_path and os.path.exists(icon_path):
        os.unlink(icon_path)
    
    # Показываем меню заново
    await show_actions_menu(query, context, user_id, is_query=True)


async def change_name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Изменить название'"""
    query = update.callback_query
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


async def change_bundle_id_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Сменить Bundle ID'"""
    query = update.callback_query
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


async def change_icon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Изменить иконку'"""
    query = update.callback_query
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


async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Назад'"""
    query = update.callback_query
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
    
    # Проверяем наличие файла в user_data
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await query.edit_message_text(MSG_FILE_NOT_FOUND)
        return
    
    # Показываем меню действий
    await show_actions_menu(query, context, user_id, is_query=True)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений - для ввода нового названия или Bundle ID"""
    user_id = update.effective_user.id
    
    # Проверяем, ждет ли бот ввода названия
    if context.user_data.get(f'waiting_name_{user_id}'):
        await handle_name_input(update, context, user_id)
        return
    
    # Проверяем, ждет ли бот ввода Bundle ID
    if context.user_data.get(f'waiting_bundle_id_{user_id}'):
        await handle_bundle_id_input(update, context, user_id)
        return
    
    # Если не ждет ввода, игнорируем сообщение


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Обработка ввода нового названия приложения"""
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


async def handle_bundle_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Обработка ввода нового Bundle ID"""
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


async def handle_photo_or_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий и документов - для загрузки иконки"""
    user_id = update.effective_user.id
    
    # Проверяем, ждет ли бот загрузки иконки
    if not context.user_data.get(f'waiting_icon_{user_id}'):
        return
    
    # Проверяем наличие архива
    archive_path = context.user_data.get(f'archive_{user_id}')
    if not archive_path or not os.path.exists(archive_path):
        await update.message.reply_text(MSG_FILE_NOT_FOUND)
        context.user_data.pop(f'waiting_icon_{user_id}', None)
        return
    
    try:
        # Получаем файл (фото или документ)
        if update.message.photo:
            # Берем фото наибольшего размера
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
        elif update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
        else:
            return
        
        # Скачиваем файл
        temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        await file.download_to_drive(temp_image.name)
        
        # Проверяем изображение
        try:
            img = Image.open(temp_image.name)
            width, height = img.size
            img_format = img.format
            
            logger.info(f"Получено изображение: формат={img_format}, размер={width}x{height}, режим={img.mode}")
            
            # Проверяем формат - принимаем JPEG, JPG и PNG
            if img_format not in ['JPEG', 'JPG', 'PNG']:
                keyboard = [[InlineKeyboardButton(BUTTON_BACK, callback_data=f"back_{user_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    MSG_ICON_INVALID_FORMAT.format(img_format or "неизвестный"),
                    reply_markup=reply_markup
                )
                os.unlink(temp_image.name)
                return
            
            # Проверяем размер
            if width != 1024 or height != 1024:
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
                # Конвертируем PNG в RGB JPEG (без альфа-канала)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Создаем белый фон для прозрачных изображений
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                else:
                    img = img.convert('RGB')
                
                # Пересохраняем как JPEG
                img.save(temp_image.name, 'JPEG', quality=95)
                logger.info("PNG успешно конвертирован в JPEG")
            
            # Все проверки пройдены
            context.user_data.pop(f'waiting_icon_{user_id}', None)
            context.user_data[f'action_new_icon_{user_id}'] = temp_image.name
            
            # Показываем обновленное меню
            await show_actions_menu(update.message, context, user_id, is_query=False)
            
        except Exception as e:
            logger.error(f"Ошибка при проверке изображения: {e}", exc_info=True)
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


def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    # Обработчик фото и документов с изображениями (для иконки)
    application.add_handler(MessageHandler(filters.PHOTO | (filters.Document.IMAGE), handle_photo_or_document))
    # Обработчик текстовых сообщений (для ввода названия или Bundle ID) - должен быть перед другими MessageHandler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    # Обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(increment_version_callback, pattern="^increment_version_"))
    application.add_handler(CallbackQueryHandler(change_name_callback, pattern="^change_name_"))
    application.add_handler(CallbackQueryHandler(change_bundle_id_callback, pattern="^change_bundle_id_"))
    application.add_handler(CallbackQueryHandler(change_icon_callback, pattern="^change_icon_"))
    application.add_handler(CallbackQueryHandler(project_info_callback, pattern="^project_info_"))
    application.add_handler(CallbackQueryHandler(get_archive_callback, pattern="^get_archive_"))
    application.add_handler(CallbackQueryHandler(reset_callback, pattern="^reset_"))
    application.add_handler(CallbackQueryHandler(back_callback, pattern="^back_"))
    
    # Запускаем бота
    logger.info(LOG_BOT_STARTED)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

