"""
Улучшенный скрипт повторного скачивания с защитой от блокировок
"""

import os
import json
import logging
import time
import random
from datetime import datetime
from document_monitor import HumanLikeDocumentMonitor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('smart_retry_downloads.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def smart_retry_with_anti_blocking():
    """Умное повторное скачивание с защитой от блокировок"""
    logger = setup_logging()
    
    logger.info("🛡️ Умное повторное скачивание с защитой от блокировок")
    logger.info("=" * 60)
    
    # Находим неудачные файлы
    try:
        with open('discovered_files.json', 'r', encoding='utf-8') as f:
            discovered_data = json.load(f)
        
        with open('downloaded_files.json', 'r', encoding='utf-8') as f:
            downloaded_data = json.load(f)
    except FileNotFoundError as e:
        logger.error(f"❌ Файл не найден: {e}")
        return
    
    failed_files = []
    for url, file_info in discovered_data.get('files', {}).items():
        is_downloaded = file_info.get('downloaded', False)
        is_in_downloads = url in downloaded_data
        
        file_exists = False
        if is_in_downloads and 'path' in downloaded_data[url]:
            file_exists = os.path.exists(downloaded_data[url]['path'])
        
        if not is_downloaded or not is_in_downloads or not file_exists:
            failed_files.append(url)
    
    if not failed_files:
        logger.info("✅ Нет файлов для повторного скачивания!")
        return
    
    logger.info(f"📊 Найдено неудачных файлов: {len(failed_files)}")
    
    # Конфигурация антиблокировки
    config = {
        'small_batch_size': 3,      # Маленькие пакеты
        'medium_batch_size': 5,     # Средние пакеты  
        'large_batch_size': 8,      # Большие пакеты (только ночью)
        'min_delay': 30,            # Минимальная задержка между файлами
        'max_delay': 90,            # Максимальная задержка
        'batch_pause': 300,         # Пауза между пакетами (5 минут)
        'session_reset_interval': 10  # Сброс сессии каждые N файлов
    }
    
    # Определяем размер пакета по времени
    current_hour = datetime.now().hour
    if 2 <= current_hour <= 6:  # Ночь - можно больше
        batch_size = config['large_batch_size']
        logger.info("🌙 Ночное время - используем большие пакеты")
    elif 9 <= current_hour <= 18:  # Рабочее время - осторожно
        batch_size = config['small_batch_size']  
        logger.info("🌞 Рабочее время - используем маленькие пакеты")
    else:  # Вечер/утро - средне
        batch_size = config['medium_batch_size']
        logger.info("🌅 Нерабочее время - используем средние пакеты")
    
    # Разбиваем на пакеты
    batches = [failed_files[i:i + batch_size] for i in range(0, len(failed_files), batch_size)]
    logger.info(f"📦 Разбито на {len(batches)} пакетов по {batch_size} файлов")
    
    # Инициализируем монитор
    try:
        monitor = HumanLikeDocumentMonitor()
        # Переключаем на улучшенный браузерный бот, если доступен
        try:
            from enhanced_browser_bot import SuperHumanBrowserBot
            monitor.browser_bot = None  # Сбрасываем старый бот
            logger.info("🚀 Используем улучшенный браузерный бот")
        except ImportError:
            logger.info("⚠️ Используем стандартный браузерный бот")
            
    except Exception as e:
        logger.error(f"❌ Не удалось инициализировать монитор: {e}")
        return
    
    total_success = 0
    total_errors = 0
    
    for batch_num, batch in enumerate(batches, 1):
        logger.info(f"\n🎯 Пакет {batch_num}/{len(batches)} ({len(batch)} файлов)")
        
        # Имитируем начало новой сессии с главной страницы
        if batch_num > 1 or True:  # Всегда начинаем с главной
            logger.info("🏠 Имитируем новую сессию - посещаем главную страницу...")
            
            bot = monitor.get_browser_bot()
            if bot:
                try:
                    # Посещаем главную страницу
                    bot.visit_page_like_human("https://court.aifc.kz")
                    time.sleep(random.uniform(10, 20))
                    
                    # Переходим в раздел законодательства
                    bot.visit_page_like_human("https://court.aifc.kz/en/legislation")
                    time.sleep(random.uniform(15, 30))
                    
                    logger.info("✅ Сессия инициализирована")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка инициализации сессии: {e}")
        
        batch_success = 0
        
        for file_num, url in enumerate(batch, 1):
            filename = os.path.basename(url)
            logger.info(f"📥 [{file_num}/{len(batch)}] {filename}")
            
            try:
                # Умная задержка перед каждым файлом
                if file_num > 1:
                    base_delay = random.uniform(config['min_delay'], config['max_delay'])
                    
                    # Увеличиваем задержку если было много ошибок
                    if total_errors > total_success and total_errors > 3:
                        base_delay *= 2
                        logger.info("⚠️ Много ошибок - увеличиваем задержку")
                    
                    logger.info(f"⏱️ Задержка: {base_delay:.1f} сек")
                    time.sleep(base_delay)
                
                # Создаем путь для сохранения
                save_dir = monitor.create_aifc_directory_structure(url, monitor.config['download_dir'])
                filename_clean = monitor.get_clean_filename(url)
                save_path = os.path.join(save_dir, filename_clean)
                
                # Пытаемся скачать с умными повторами
                success = smart_download_with_retries(monitor, url, save_path, logger)
                
                if success:
                    batch_success += 1
                    total_success += 1
                    
                    # Обновляем статус
                    if url in monitor.discovered_files['files']:
                        monitor.discovered_files['files'][url]['downloaded'] = True
                        monitor.discovered_files['files'][url]['last_downloaded'] = datetime.now().isoformat()
                        monitor.discovered_files['files'][url]['is_new'] = False
                    
                    logger.info(f"✅ Успешно скачан: {filename_clean}")
                else:
                    total_errors += 1
                    logger.warning(f"❌ Не удалось скачать: {filename}")
                
                # Сохраняем прогресс
                monitor.save_downloaded_history()
                monitor.save_discovered_files()
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке {url}: {e}")
                total_errors += 1
        
        # Статистика пакета
        batch_success_rate = batch_success / len(batch) if batch else 0
        logger.info(f"📊 Пакет завершен: {batch_success}/{len(batch)} ({batch_success_rate:.1%})")
        
        # Длинная пауза между пакетами
        if batch_num < len(batches):
            pause_time = config['batch_pause'] + random.uniform(-60, 120)
            logger.info(f"😴 Пауза между пакетами: {pause_time:.0f} сек")
            time.sleep(pause_time)
            
            # Сброс браузерной сессии для следующего пакета
            if monitor.browser_bot:
                try:
                    monitor.browser_bot.close()
                    monitor.browser_bot = None
                    logger.info("🔄 Браузерная сессия сброшена")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка сброса сессии: {e}")
    
    # Финальная статистика
    total_files = len(failed_files)
    final_success_rate = total_success / total_files if total_files > 0 else 0
    
    logger.info("=" * 60)
    logger.info("🏁 ФИНАЛЬНАЯ СТАТИСТИКА:")
    logger.info(f"✅ Успешно скачано: {total_success}")
    logger.info(f"❌ Ошибок: {total_errors}")
    logger.info(f"📋 Всего попыток: {total_files}")
    logger.info(f"📈 Успешность: {final_success_rate:.1%}")
    
    # Закрываем браузер
    if monitor.browser_bot:
        try:
            monitor.browser_bot.close()
        except:
            pass
    
    if total_success > 0:
        logger.info("🎉 Умное скачивание завершено успешно!")
    else:
        logger.info("😞 Файлы все еще не удается скачать. Возможно, они недоступны на сайте.")

def smart_download_with_retries(monitor, url, save_path, logger, max_retries=3):
    """Умное скачивание с продвинутыми повторами"""
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"🔄 Попытка {attempt + 1}/{max_retries}: {os.path.basename(url)}")
            
            # Увеличивающиеся задержки
            if attempt > 0:
                retry_delay = [10, 30, 60][min(attempt-1, 2)]
                jitter = random.uniform(-5, 15)
                total_delay = retry_delay + jitter
                
                logger.info(f"⏳ Задержка перед повтором: {total_delay:.1f} сек")
                time.sleep(total_delay)
            
            # Пытаемся скачать
            result = monitor.download_with_browser_bot(url, save_path)
            
            if result in ["new", "updated"]:
                return True
            elif result == "unchanged":
                logger.info("ℹ️ Файл уже существует и не изменился")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка на попытке {attempt + 1}: {e}")
            
            # При ошибке делаем дополнительную паузу
            if attempt < max_retries - 1:
                error_delay = random.uniform(20, 60)
                logger.info(f"😴 Пауза после ошибки: {error_delay:.1f} сек")
                time.sleep(error_delay)
    
    return False

if __name__ == "__main__":
    print("🛡️ Умное повторное скачивание с защитой от блокировок")
    print("=" * 60)
    
    confirm = input("🚀 Запустить умное скачивание? (да/нет): ")
    if confirm.lower() in ['да', 'yes', 'y']:
        smart_retry_with_anti_blocking()
    else:
        print("❌ Операция отменена")
