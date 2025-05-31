#!/usr/bin/env python3
"""
Скрипт проверки и настройки системы для AIFC Court Monitor
"""

import sys
import subprocess
import importlib
import os
import json
import requests

def check_python_version():
    """Проверка версии Python"""
    print("🐍 Проверка версии Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Требуется Python 3.7+, установлен {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    required_packages = {
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'schedule': 'schedule'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {package_name} - установлен")
        except ImportError:
            print(f"❌ {package_name} - НЕ установлен")
            missing_packages.append(package_name)
    
    return missing_packages

def install_dependencies(packages):
    """Установка недостающих зависимостей"""
    if not packages:
        return True
    
    print(f"\n🔧 Установка недостающих пакетов: {', '.join(packages)}")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install"
        ] + packages)
        print("✅ Все зависимости установлены!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка при установке зависимостей")
        return False

def check_internet_connection():
    """Проверка интернет-соединения"""
    print("\n🌐 Проверка интернет-соединения...")
    
    try:
        response = requests.get("https://court.aifc.kz", timeout=10)
        if response.status_code == 200:
            print("✅ Соединение с court.aifc.kz - OK")
            return True
        else:
            print(f"⚠️ Сайт недоступен (код: {response.status_code})")
            return False
    except requests.RequestException as e:
        print(f"❌ Ошибка соединения: {str(e)}")
        return False

def create_default_config():
    """Создание конфигурационного файла по умолчанию"""
    print("\n⚙️ Создание конфигурационного файла...")
    
    config = {
        "urls": [
            "https://court.aifc.kz/en/judgments",
            "https://court.aifc.kz/en/legislation"
        ],
        "download_dir": "aifc_documents",
        "check_interval_minutes": 120,
        "file_extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".zip", ".rar"],
        "max_depth": 3,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "timeout": 30,
        "special_patterns": {
            "aifc_court": {
                "base_url": "https://court.aifc.kz",
                "judgment_selector": "a[href*='/uploads/']",
                "download_link_selector": "a[href*='.pdf'], a[href*='.doc'], a[href*='.docx']",
                "folder_mapping": {
                    "judgments": "Judgments",
                    "legislation": "Legislation"
                }
            }
        }
    }
    
    config_file = "aifc_monitor_config.json"
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"✅ Создан файл конфигурации: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания конфигурации: {str(e)}")
        return False

def check_files():
    """Проверка наличия необходимых файлов"""
    print("\n📁 Проверка файлов программы...")
    
    required_files = [
        'document_monitor.py',
        'run_aifc_monitor.py',
        'requirements.txt'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name} - найден")
        else:
            print(f"❌ {file_name} - НЕ найден")
            missing_files.append(file_name)
    
    return missing_files

def test_basic_functionality():
    """Тестирование базовой функциональности"""
    print("\n🧪 Тестирование базовой функциональности...")
    
    try:
        # Тестируем импорт основного модуля
        sys.path.insert(0, '.')
        import document_monitor
        print("✅ Основной модуль загружается корректно")
        
        # Тестируем создание экземпляра
        monitor = document_monitor.DocumentMonitor('aifc_monitor_config.json')
        print("✅ Монитор создается успешно")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        return False

def main():
    """Основная функция проверки"""
    print("=" * 50)
    print("    AIFC Court Monitor - Проверка системы")
    print("=" * 50)
    
    all_ok = True
    
    # Проверка версии Python
    if not check_python_version():
        all_ok = False
    
    # Проверка файлов
    missing_files = check_files()
    if missing_files:
        print(f"\n❌ Отсутствуют файлы: {', '.join(missing_files)}")
        print("Пожалуйста, скачайте все необходимые файлы программы.")
        all_ok = False
    
    # Проверка зависимостей
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n🔧 Попытка установки недостающих зависимостей...")
        if not install_dependencies(missing_deps):
            all_ok = False
    
    # Проверка интернет-соединения
    if not check_internet_connection():
        print("⚠️ Проблемы с интернет-соединением могут повлиять на работу")
    
    # Создание конфигурации
    if not os.path.exists('aifc_monitor_config.json'):
        if not create_default_config():
            all_ok = False
    else:
        print("\n⚙️ Конфигурационный файл уже существует")
    
    # Тестирование функциональности
    if all_ok and not missing_files:
        if not test_basic_functionality():
            all_ok = False
    
    # Итоговый результат
    print("\n" + "=" * 50)
    if all_ok:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("\nТеперь вы можете запустить программу:")
        print("  python run_aifc_monitor.py --once     # Однократная проверка")
        print("  python run_aifc_monitor.py            # Непрерывный мониторинг")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("Исправьте указанные проблемы и запустите проверку снова.")
    
    print("=" * 50)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())