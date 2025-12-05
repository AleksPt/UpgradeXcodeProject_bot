#!/usr/bin/env python3
"""Скрипт для проверки структуры проекта."""

import sys
from pathlib import Path

# Проверяем структуру директорий
required_structure = {
    "telegram_xcode_bot": {
        "__init__.py": True,
        "__main__.py": True,
        "config.py": True,
        "logger.py": True,
        "exceptions.py": True,
        "handlers": {
            "__init__.py": True,
            "command_handlers.py": True,
            "document_handlers.py": True,
            "callback_handlers.py": True,
            "input_handlers.py": True,
            "helpers.py": True,
        },
        "services": {
            "__init__.py": True,
            "xcode_service.py": True,
            "archive_service.py": True,
            "icon_service.py": True,
        },
        "utils": {
            "__init__.py": True,
            "validators.py": True,
            "version_utils.py": True,
        }
    },
    "tests": {
        "__init__.py": True,
        "conftest.py": True,
        "test_validators.py": True,
        "test_xcode_service.py": True,
        "fixtures": {}
    },
    "main.py": True,
    "requirements.txt": True,
    "requirements-dev.txt": True,
    "README.md": True,
    "CHANGELOG.md": True,
    "Procfile": True,
}


def check_structure(base_path: Path, structure: dict, prefix: str = "") -> bool:
    """Рекурсивно проверяет структуру проекта."""
    all_good = True
    
    for name, content in structure.items():
        path = base_path / name
        
        if isinstance(content, dict):
            # Это директория
            if not path.is_dir():
                print(f"❌ {prefix}{name}/ - директория не найдена")
                all_good = False
            else:
                print(f"✅ {prefix}{name}/")
                if not check_structure(path, content, prefix + "  "):
                    all_good = False
        else:
            # Это файл
            if not path.is_file():
                print(f"❌ {prefix}{name} - файл не найден")
                all_good = False
            else:
                print(f"✅ {prefix}{name}")
    
    return all_good


def main():
    """Основная функция проверки."""
    project_root = Path(__file__).parent
    
    print("=" * 60)
    print("Проверка структуры проекта Telegram Xcode Bot")
    print("=" * 60)
    print()
    
    if check_structure(project_root, required_structure):
        print()
        print("=" * 60)
        print("✅ Все файлы и директории на месте!")
        print("=" * 60)
        return 0
    else:
        print()
        print("=" * 60)
        print("❌ Некоторые файлы или директории отсутствуют!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

