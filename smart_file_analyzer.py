"""
Умный анализатор файлов с правильной логикой проверки
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from document_monitor import HumanLikeDocumentMonitor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('smart_file_analyzer.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_file_hash(filepath):
    """Получение хеша файла"""
    try:
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception:
        return None

def analyze_file_status():
    """Анализ реального статуса файлов"""
    logger = setup_logging()
    
    logger.info("🔍 Анализ реального статуса файлов...")
    logger.info("=" * 60)
    
    # Загружаем данные
    try:
        with open('discovered_files.json', 'r', encoding='utf-8') as f:
            discovered_data = json.load(f)
        
        with open('downloaded_files.json', 'r', encoding='utf-8') as f:
            downloaded_data = json.load(f)
    except FileNotFoundError as e:
        logger.error(f"❌ Файл не найден: {e}")
        return
    
    monitor = HumanLikeDocumentMonitor()
    
    # Анализируем каждый файл
    file_status = {
        'missing_completely': [],      # Файла нет вообще
        'missing_on_disk': [],         # Запись есть, файла нет
        'outdated_records': [],        # Файл есть, запись устарела
        'correctly_tracked': [],       # Все правильно
        'needs_redownload': []         # Нужно перескачать
    }
    
    total_files = len(discovered_data.get('files', {}))
    logger.info(f"📊 Всего обнаруженных файлов: {total_files}")
    
    for i, (url, file_info) in enumerate(discovered_data.get('files', {}).items(), 1):
        filename = os.path.basename(url)
        logger.debug(f"🔍 [{i}/{total_files}] Анализируем: {filename}")
        
        # 1. Определяем где должен быть файл
        expected_dir = monitor.create_aifc_directory_structure(url, monitor.config['download_dir'])
        expected_filename = monitor.get_clean_filename(url)
        expected_path = os.path.join(expected_dir, expected_filename)
        
        # 2. Проверяем существует ли файл на диске
        file_exists_on_disk = os.path.exists(expected_path)
        
        # 3. Проверяем запись в downloaded_files.json
        is_in_download_records = url in downloaded_data
        
        # 4. Проверяем пометку в discovered_files.json
        is_marked_downloaded = file_info.get('downloaded', False)
        
        # 5. Анализируем статус
        if not file_exists_on_disk and not is_in_download_records:
            # Файла нет совсем - нужно скачать
            file_status['missing_completely'].append({
                'url': url,
                'expected_path': expected_path,
                'reason': 'Файл не скачан'
            })
            
        elif not file_exists_on_disk and is_in_download_records:
            # Запись есть, но файл потерян - нужно перескачать
            file_status['missing_on_disk'].append({
                'url': url,
                'expected_path': expected_path,
                'recorded_path': downloaded_data[url].get('path', 'unknown'),
                'reason': 'Файл потерян с диска'
            })
            
        elif file_exists_on_disk and not is_marked_downloaded:
            # Файл есть, но не помечен как скачанный - обновить записи
            file_status['outdated_records'].append({
                'url': url,
                'existing_path': expected_path,
                'reason': 'Нужно обновить записи'
            })
            
        elif file_exists_on_disk and is_marked_downloaded and is_in_download_records:
            # Все правильно
            file_status['correctly_tracked'].append({
                'url': url,
                'path': expected_path,
                'reason': 'Отслеживается корректно'
            })
            
        else:
            # Неопределенный случай - нужно разобраться
            file_status['needs_redownload'].append({
                'url': url,
                'expected_path': expected_path,
                'reason': f"Неопределенный статус (exists:{file_exists_on_disk}, marked:{is_marked_downloaded}, recorded:{is_in_download_records})"
            })
    
    # Выводим статистику
    logger.info("📋 АНАЛИЗ СТАТУСА ФАЙЛОВ:")
    logger.info(f"❌ Не скачаны совсем: {len(file_status['missing_completely'])}")
    logger.info(f"💾 Потеряны с диска: {len(file_status['missing_on_disk'])}")
    logger.info(f"📝 Устаревшие записи: {len(file_status['outdated_records'])}")
    logger.info(f"✅ Отслеживаются правильно: {len(file_status['correctly_tracked'])}")
    logger.info(f"❓ Неопределенный статус: {len(file_status['needs_redownload'])}")
    
    # Детальная информация по каждой категории
    for category, files in file_status.items():
        if files and category != 'correctly_tracked':  # Правильные файлы не показываем
            logger.info(f"\n📋 {category.upper()}:")
            for file_info in files[:5]:  # Показываем первые 5
                logger.info(f"   • {os.path.basename(file_info['url'])}")
                logger.info(f"     Причина: {file_info['reason']}")
            if len(files) > 5:
                logger.info(f"   ... и еще {len(files) - 5} файлов")
    
    return file_status

def fix_file_records():
    """Исправление записей о файлах"""
    logger = setup_logging()
    
    logger.info("🔧 Исправление записей о файлах...")
    
    # Получаем анализ
    file_status = analyze_file_status()
    
    # Исправляем устаревшие записи
    outdated_files = file_status['outdated_records']
    
    if outdated_files:
        logger.info(f"📝 Исправляем {len(outdated_files)} устаревших записей...")
        
        # Загружаем данные
        with open('discovered_files.json', 'r', encoding='utf-8') as f:
            discovered_data = json.load(f)
        
        with open('downloaded_files.json', 'r', encoding='utf-8') as f:
            downloaded_data = json.load(f)
        
        for file_info in outdated_files:
            url = file_info['url']
            existing_path = file_info['existing_path']
            
            try:
                # Получаем хеш существующего файла
                file_hash = get_file_hash(existing_path)
                file_size = os.path.getsize(existing_path)
                
                # Обновляем discovered_files.json
                if url in discovered_data['files']:
                    discovered_data['files'][url]['downloaded'] = True
                    discovered_data['files'][url]['last_downloaded'] = datetime.now().isoformat()
                    discovered_data['files'][url]['is_new'] = False
                
                # Обновляем downloaded_files.json
                downloaded_data[url] = {
                    'hash': file_hash,
                    'path': existing_path,
                    'downloaded_at': datetime.now().isoformat(),
                    'size': file_size,
                    'method': 'existing_file_registered'
                }
                
                logger.info(f"✅ Обновлена запись: {os.path.basename(existing_path)}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка обновления записи для {url}: {e}")
        
        # Сохраняем обновленные файлы
        with open('discovered_files.json', 'w', encoding='utf-8') as f:
            json.dump(discovered_data, f, indent=2, ensure_ascii=False)
        
        with open('downloaded_files.json', 'w', encoding='utf-8') as f:
            json.dump(downloaded_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Записи обновлены и сохранены")
    
    else:
        logger.info("✅ Нет устаревших записей для исправления")

def get_truly_missing_files():
    """Получение списка файлов, которые действительно нужно скачать"""
    logger = setup_logging()
    
    # Сначала исправляем записи
    fix_file_records()
    
    # Затем анализируем заново
    file_status = analyze_file_status()
    
    truly_missing = []
    truly_missing.extend(file_status['missing_completely'])
    truly_missing.extend(file_status['missing_on_disk'])
    truly_missing.extend(file_status['needs_redownload'])
    
    logger.info(f"\n🎯 ФАЙЛЫ ДЛЯ СКАЧИВАНИЯ:")
    logger.info(f"📥 Действительно нужно скачать: {len(truly_missing)} файлов")
    
    if truly_missing:
        logger.info("\n📋 Список файлов для скачивания:")
        for file_info in truly_missing:
            logger.info(f"   • {os.path.basename(file_info['url'])}")
            logger.info(f"     Причина: {file_info['reason']}")
    else:
        logger.info("🎉 Все файлы уже скачаны! Дополнительное скачивание не требуется.")
    
    return [f['url'] for f in truly_missing]

if __name__ == "__main__":
    print("🔍 Умный анализатор файлов")
    print("=" * 50)
    
    choice = input("Выберите действие:\n1. Анализ статуса файлов\n2. Исправление записей\n3. Получить список для скачивания\nВаш выбор (1-3): ")
    
    if choice == "1":
        analyze_file_status()
    elif choice == "2":
        fix_file_records()
    elif choice == "3":
        missing_files = get_truly_missing_files()
        if missing_files:
            print(f"\n📋 Найдено {len(missing_files)} файлов для скачивания")
        else:
            print("\n🎉 Все файлы уже скачаны!")
    else:
        print("❌ Неверный выбор")