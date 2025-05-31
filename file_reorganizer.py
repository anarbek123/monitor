"""
Скрипт для реорганизации уже скачанных файлов по правильным папкам
"""

import os
import json
import shutil
import logging
from pathlib import Path
from urllib.parse import urlparse

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('file_reorganizer.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_downloaded_files():
    """Загрузка информации о скачанных файлах"""
    try:
        with open('downloaded_files.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл downloaded_files.json не найден!")
        return {}

def classify_url(url):
    """Классификация URL для определения правильной папки"""
    url_lower = url.lower()
    
    # Судебные решения и дела
    if any(keyword in url_lower for keyword in [
        'judgments', '/uploads/', 'case%20no', 'judgment', 
        'case_no', 'case-no', 'decision', 'ruling'
    ]):
        return 'Judgments'
    
    # Законодательство и правила
    elif any(keyword in url_lower for keyword in [
        'legislation', '/legals/', 'regulations', 'rules', 
        'policy', 'consultation-paper', 'guidance', 'notice',
        'amendment', 'circular', 'directive', 'order'
    ]):
        return 'Legislation'
    
    # Специфические ключевые слова AIFC
    elif any(keyword in url_lower for keyword in [
        'aifc-court-regulations', 'aifc-court-rules', 
        'template-of-offering', 'afsa-policy'
    ]):
        return 'Legislation'
    
    else:
        return 'Other_Documents'

def get_correct_path(url, base_dir):
    """Получение правильного пути для файла"""
    folder_name = classify_url(url)
    
    # Создаем основную структуру
    correct_path = os.path.join(base_dir, 'AIFC_Court', folder_name)
    
    # Для решений судов создаем подпапки по годам
    if folder_name == 'Judgments':
        import re
        year_match = re.search(r'20\d{2}', url)
        if year_match:
            year = year_match.group()
            correct_path = os.path.join(correct_path, year)
    
    # Для законодательства создаем подпапки по типу
    elif folder_name == 'Legislation':
        url_lower = url.lower()
        if 'consultation-paper' in url_lower:
            correct_path = os.path.join(correct_path, 'Consultation_Papers')
        elif 'guidance' in url_lower:
            correct_path = os.path.join(correct_path, 'Guidance_Documents')
        elif 'notice' in url_lower:
            correct_path = os.path.join(correct_path, 'Notices')
        elif 'template' in url_lower:
            correct_path = os.path.join(correct_path, 'Templates')
    
    return correct_path

def reorganize_files():
    """Основная функция реорганизации файлов"""
    logger = setup_logging()
    
    logger.info("🚀 Начинаем реорганизацию файлов...")
    
    # Загружаем информацию о скачанных файлах
    downloaded_files = load_downloaded_files()
    
    if not downloaded_files:
        logger.error("❌ Нет информации о скачанных файлах")
        return
    
    base_dir = "aifc_documents"
    moved_count = 0
    error_count = 0
    already_correct_count = 0
    
    logger.info(f"📊 Всего файлов для проверки: {len(downloaded_files)}")
    
    for url, file_info in downloaded_files.items():
        try:
            current_path = file_info.get('path', '')
            
            if not current_path or not os.path.exists(current_path):
                logger.warning(f"⚠️ Файл не найден: {current_path}")
                error_count += 1
                continue
            
            # Определяем правильный путь
            correct_dir = get_correct_path(url, base_dir)
            filename = os.path.basename(current_path)
            correct_path = os.path.join(correct_dir, filename)
            
            # Проверяем, нужно ли перемещать
            if os.path.normpath(current_path) == os.path.normpath(correct_path):
                logger.debug(f"✅ Файл уже в правильной папке: {filename}")
                already_correct_count += 1
                continue
            
            # Создаем целевую папку
            os.makedirs(correct_dir, exist_ok=True)
            
            # Если целевой файл уже существует, создаем резервную копию
            if os.path.exists(correct_path):
                backup_path = correct_path + ".backup"
                counter = 1
                while os.path.exists(backup_path):
                    backup_path = f"{correct_path}.backup{counter}"
                    counter += 1
                
                shutil.move(correct_path, backup_path)
                logger.info(f"🔄 Создана резервная копия: {os.path.basename(backup_path)}")
            
            # Перемещаем файл
            shutil.move(current_path, correct_path)
            
            # Обновляем путь в базе данных
            downloaded_files[url]['path'] = correct_path
            downloaded_files[url]['moved_at'] = str(Path().cwd())
            
            logger.info(f"📁 Перемещен: {filename}")
            logger.info(f"   Из: {current_path}")
            logger.info(f"   В:  {correct_path}")
            
            moved_count += 1
            
            # Сохраняем прогресс каждые 10 файлов
            if moved_count % 10 == 0:
                save_updated_database(downloaded_files)
                logger.info(f"💾 Прогресс сохранен: {moved_count} файлов перемещено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке {url}: {e}")
            error_count += 1
    
    # Сохраняем обновленную базу данных
    save_updated_database(downloaded_files)
    
    # Выводим статистику
    logger.info("=" * 50)
    logger.info("📊 СТАТИСТИКА РЕОРГАНИЗАЦИИ:")
    logger.info(f"📁 Файлов перемещено: {moved_count}")
    logger.info(f"✅ Уже в правильных папках: {already_correct_count}")
    logger.info(f"❌ Ошибок: {error_count}")
    logger.info(f"📋 Всего обработано: {len(downloaded_files)}")
    
    # Очищаем пустые папки
    cleanup_empty_directories(base_dir)
    
    logger.info("🎉 Реорганизация завершена!")

def save_updated_database(downloaded_files):
    """Сохранение обновленной базы данных"""
    with open('downloaded_files.json', 'w', encoding='utf-8') as f:
        json.dump(downloaded_files, f, indent=2, ensure_ascii=False)

def cleanup_empty_directories(base_dir):
    """Удаление пустых папок"""
    logger = logging.getLogger(__name__)
    
    try:
        for root, dirs, files in os.walk(base_dir, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    # Пытаемся удалить папку (удалится только если пустая)
                    os.rmdir(dir_path)
                    logger.info(f"🗑️ Удалена пустая папка: {dir_path}")
                except OSError:
                    # Папка не пустая - это нормально
                    pass
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при очистке пустых папок: {e}")

def preview_reorganization():
    """Предварительный просмотр изменений без фактического перемещения"""
    logger = setup_logging()
    
    logger.info("👀 Предварительный просмотр реорганизации...")
    
    downloaded_files = load_downloaded_files()
    
    if not downloaded_files:
        return
    
    base_dir = "aifc_documents"
    changes = []
    
    for url, file_info in downloaded_files.items():
        current_path = file_info.get('path', '')
        
        if not current_path:
            continue
        
        correct_dir = get_correct_path(url, base_dir)
        filename = os.path.basename(current_path)
        correct_path = os.path.join(correct_dir, filename)
        
        if os.path.normpath(current_path) != os.path.normpath(correct_path):
            changes.append({
                'filename': filename,
                'current': current_path,
                'correct': correct_path,
                'url': url
            })
    
    if changes:
        logger.info(f"📋 Планируется переместить {len(changes)} файлов:")
        
        # Группируем по типам
        by_type = {}
        for change in changes:
            folder_type = classify_url(change['url'])
            if folder_type not in by_type:
                by_type[folder_type] = []
            by_type[folder_type].append(change)
        
        for folder_type, files in by_type.items():
            logger.info(f"\n📂 {folder_type}: {len(files)} файлов")
            for file_info in files[:5]:  # Показываем первые 5
                logger.info(f"   • {file_info['filename']}")
            if len(files) > 5:
                logger.info(f"   ... и еще {len(files) - 5} файлов")
    else:
        logger.info("✅ Все файлы уже находятся в правильных папках!")

if __name__ == "__main__":
    print("🔧 Утилита реорганизации файлов AIFC Court")
    print("=" * 50)
    
    choice = input("Выберите действие:\n1. Предварительный просмотр\n2. Выполнить реорганизацию\nВаш выбор (1/2): ")
    
    if choice == "1":
        preview_reorganization()
    elif choice == "2":
        confirm = input("⚠️ Это переместит файлы! Продолжить? (да/нет): ")
        if confirm.lower() in ['да', 'yes', 'y']:
            reorganize_files()
        else:
            print("❌ Операция отменена")
    else:
        print("❌ Неверный выбор")