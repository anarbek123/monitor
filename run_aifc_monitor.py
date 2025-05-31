"""
Единый автоматизированный AIFC монитор документов
Все функции в одном файле - запускается одной командой
"""

import os
import sys
import json
import logging
import hashlib
import time
import shutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from document_monitor import HumanLikeDocumentMonitor

class UnifiedAIFCMonitor:
    def __init__(self):
        self.monitor = HumanLikeDocumentMonitor()
        self.logger = self.setup_logging()
        self.session_report = {
            'start_time': datetime.now(),
            'discovered_files': 0,
            'new_files': 0,
            'updated_files': 0,
            'unchanged_files': 0,
            'download_errors': 0,
            'total_downloaded': 0,
            'version_updates': 0,
            'errors': []
        }
        
    def setup_logging(self):
        """Настройка логирования"""
        log_filename = f"aifc_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def run_full_automation(self):
        """Полный автоматический цикл мониторинга"""
        self.logger.info("🚀 АВТОМАТИЧЕСКИЙ МОНИТОРИНГ AIFC ДОКУМЕНТОВ")
        self.logger.info("=" * 60)
        self.logger.info(f"⏰ Начало сессии: {self.session_report['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Шаг 1: Анализ существующей базы данных
            self.logger.info("\n📊 Шаг 1: Анализ существующей базы данных...")
            local_status = self.analyze_local_database()
            
            # Шаг 2: Анализ файлов на диске и исправление записей
            self.logger.info("\n🔍 Шаг 2: Анализ файлов на диске...")
            file_status = self.analyze_and_fix_file_records()
            
            # Шаг 3: Определение файлов для скачивания
            self.logger.info("\n🎯 Шаг 3: Определение файлов для скачивания...")
            files_to_download = self.get_files_to_download()
            
            if not files_to_download:
                self.logger.info("✅ Все файлы уже скачаны!")
                # Но все равно проверим сайт на новые документы
                self.logger.info("\n🌐 Проверяем сайт на новые документы...")
                self.scan_website_for_updates()
                files_to_download = self.get_files_to_download()
            
            # Шаг 4: Скачивание новых и недостающих файлов
            if files_to_download:
                self.logger.info(f"\n📥 Шаг 4: Скачивание {len(files_to_download)} файлов...")
                download_results = self.download_files_smart(files_to_download)
            else:
                self.logger.info("\n✅ Скачивание не требуется - все файлы актуальны")
                download_results = {'successful': 0, 'failed': 0}
            
            # Шаг 5: Организация файлов по папкам
            self.logger.info("\n📁 Шаг 5: Организация файлов...")
            self.organize_files_automatically()
            
            # Шаг 6: Генерация отчета
            self.logger.info("\n📊 Шаг 6: Генерация отчета...")
            final_report = self.generate_final_report()
            
            return final_report
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            self.session_report['errors'].append(f"Критическая ошибка: {e}")
            return self.generate_error_report(e)
    
    def analyze_local_database(self):
        """Анализ существующей локальной базы данных"""
        try:
            discovered_files = self.monitor.load_discovered_files()
            downloaded_files = self.monitor.load_downloaded_history()
            
            local_count = len(discovered_files.get('files', {}))
            downloaded_count = len(downloaded_files)
            
            self.logger.info(f"📋 Файлов в базе обнаружения: {local_count}")
            self.logger.info(f"📥 Файлов в базе скачивания: {downloaded_count}")
            
            self.session_report['discovered_files'] = local_count
            
            return {
                'discovered_count': local_count,
                'downloaded_count': downloaded_count,
                'last_scan': discovered_files.get('last_scan', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа локальной базы: {e}")
            return {'error': str(e)}
    
    def analyze_and_fix_file_records(self):
        """Анализ файлов на диске и исправление записей"""
        try:
            discovered_files = self.monitor.discovered_files
            downloaded_files = self.monitor.downloaded_files
            
            file_status = {
                'missing_completely': [],
                'missing_on_disk': [],
                'outdated_records': [],
                'correctly_tracked': []
            }
            
            fixed_records = 0
            
            for url, file_info in discovered_files.get('files', {}).items():
                # Определяем ожидаемый путь файла
                expected_dir = self.monitor.create_aifc_directory_structure(url, self.monitor.config['download_dir'])
                expected_filename = self.monitor.get_clean_filename(url)
                expected_path = os.path.join(expected_dir, expected_filename)
                
                # Проверяем состояние файла
                file_exists_on_disk = os.path.exists(expected_path)
                is_in_download_records = url in downloaded_files
                is_marked_downloaded = file_info.get('downloaded', False)
                
                if not file_exists_on_disk and not is_in_download_records:
                    # Файл не скачан
                    file_status['missing_completely'].append(url)
                    
                elif not file_exists_on_disk and is_in_download_records:
                    # Файл потерян с диска
                    file_status['missing_on_disk'].append(url)
                    
                elif file_exists_on_disk and not is_marked_downloaded:
                    # Файл есть, но не помечен - исправляем
                    file_status['outdated_records'].append(url)
                    self.fix_file_record(url, expected_path)
                    fixed_records += 1
                    
                else:
                    # Все правильно
                    file_status['correctly_tracked'].append(url)
            
            self.logger.info(f"✅ Файлов отслеживается корректно: {len(file_status['correctly_tracked'])}")
            self.logger.info(f"❌ Не скачано: {len(file_status['missing_completely'])}")
            self.logger.info(f"💾 Потеряно с диска: {len(file_status['missing_on_disk'])}")
            self.logger.info(f"🔧 Исправлено записей: {fixed_records}")
            
            if fixed_records > 0:
                self.monitor.save_discovered_files()
                self.monitor.save_downloaded_history()
            
            return file_status
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа файлов: {e}")
            return {}
    
    def fix_file_record(self, url, file_path):
        """Исправление записи о файле"""
        try:
            # Получаем хеш файла
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            file_size = os.path.getsize(file_path)
            
            # Обновляем discovered_files
            if url in self.monitor.discovered_files['files']:
                self.monitor.discovered_files['files'][url]['downloaded'] = True
                self.monitor.discovered_files['files'][url]['last_downloaded'] = datetime.now().isoformat()
                self.monitor.discovered_files['files'][url]['is_new'] = False
            
            # Обновляем downloaded_files
            self.monitor.downloaded_files[url] = {
                'hash': file_hash,
                'path': file_path,
                'downloaded_at': datetime.now().isoformat(),
                'size': file_size,
                'method': 'record_fixed'
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось исправить запись для {url}: {e}")
    
    def get_files_to_download(self):
        """Получение списка файлов для скачивания"""
        files_to_download = []
        
        for url, file_info in self.monitor.discovered_files.get('files', {}).items():
            is_downloaded = file_info.get('downloaded', False)
            
            if not is_downloaded:
                files_to_download.append(url)
                continue
            
            # Проверяем существует ли файл на диске
            if url in self.monitor.downloaded_files:
                file_path = self.monitor.downloaded_files[url].get('path')
                if file_path and not os.path.exists(file_path):
                    files_to_download.append(url)
        
        return files_to_download
    
    def scan_website_for_updates(self):
        """Быстрое сканирование сайта на обновления"""
        try:
            sections_to_scan = [
                '/en/legislation',
                '/en/judgments',
                '/en/fees',
                '/en/practice-directions'
            ]
            
            before_count = len(self.monitor.discovered_files.get('files', {}))
            
            for section in sections_to_scan:
                self.logger.info(f"📄 Быстрое сканирование: {section}")
                try:
                    self.monitor.discover_files_from_section(section)
                    time.sleep(3)  # Короткая пауза
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка сканирования {section}: {e}")
            
            after_count = len(self.monitor.discovered_files.get('files', {}))
            new_discoveries = after_count - before_count
            
            if new_discoveries > 0:
                self.logger.info(f"🆕 Найдено новых файлов: {new_discoveries}")
                self.monitor.save_discovered_files()
            else:
                self.logger.info("ℹ️ Новых файлов не найдено")
            
            return new_discoveries
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сканирования сайта: {e}")
            return 0
    
    def download_files_smart(self, files_to_download):
        """Умное скачивание файлов с защитой от блокировок"""
        successful_downloads = 0
        failed_downloads = 0
        
        total_files = len(files_to_download)
        
        # Определяем размер пакета в зависимости от времени
        current_hour = datetime.now().hour
        if 2 <= current_hour <= 6:  # Ночь
            batch_size = 8
            base_delay = (10, 30)
        elif 9 <= current_hour <= 18:  # Рабочее время
            batch_size = 3
            base_delay = (30, 90)
        else:  # Вечер/утро
            batch_size = 5
            base_delay = (20, 60)
        
        self.logger.info(f"📦 Размер пакета: {batch_size}, задержка: {base_delay[0]}-{base_delay[1]} сек")
        
        # Разбиваем на пакеты
        batches = [files_to_download[i:i + batch_size] for i in range(0, total_files, batch_size)]
        
        for batch_num, batch in enumerate(batches, 1):
            self.logger.info(f"\n🎯 Пакет {batch_num}/{len(batches)} ({len(batch)} файлов)")
            
            for file_num, url in enumerate(batch, 1):
                filename = os.path.basename(url)
                self.logger.info(f"📥 [{file_num}/{len(batch)}] {filename}")
                
                try:
                    # Определяем путь сохранения
                    save_dir = self.monitor.create_aifc_directory_structure(url, self.monitor.config['download_dir'])
                    clean_filename = self.monitor.get_clean_filename(url)
                    save_path = os.path.join(save_dir, clean_filename)
                    
                    # Скачиваем файл
                    success = self.download_single_file_with_retry(url, save_path)
                    
                    if success:
                        successful_downloads += 1
                        self.session_report['total_downloaded'] += 1
                        self.logger.info(f"✅ Успешно: {clean_filename}")
                    else:
                        failed_downloads += 1
                        self.session_report['download_errors'] += 1
                        self.logger.warning(f"❌ Неудача: {filename}")
                    
                    # Задержка между файлами
                    if file_num < len(batch):
                        delay = time.sleep(random.uniform(*base_delay))
                
                except Exception as e:
                    failed_downloads += 1
                    self.session_report['download_errors'] += 1
                    self.logger.error(f"❌ Ошибка {filename}: {e}")
            
            # Пауза между пакетами
            if batch_num < len(batches):
                pause_time = 180 + random.uniform(-30, 60)  # 2.5-4 минуты
                self.logger.info(f"😴 Пауза между пакетами: {pause_time:.0f} сек")
                time.sleep(pause_time)
        
        self.logger.info(f"\n📊 ИТОГИ СКАЧИВАНИЯ:")
        self.logger.info(f"✅ Успешно: {successful_downloads}")
        self.logger.info(f"❌ Ошибок: {failed_downloads}")
        
        return {'successful': successful_downloads, 'failed': failed_downloads}
    
    def download_single_file_with_retry(self, url, save_path, max_retries=3):
        """Скачивание одного файла с повторами"""
        import random
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    retry_delay = [10, 30, 60][min(attempt-1, 2)] + random.uniform(-5, 15)
                    self.logger.debug(f"⏳ Задержка перед повтором: {retry_delay:.1f} сек")
                    time.sleep(retry_delay)
                
                # Метод 1: Прямое скачивание
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/octet-stream,*/*',
                    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                    'Referer': 'https://court.aifc.kz/en/legislation'
                }
                
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    # Проверяем размер файла
                    if os.path.getsize(save_path) > 1000:  # Больше 1KB
                        self.update_file_records(url, save_path)
                        return True
                    else:
                        os.remove(save_path)
                        self.logger.warning(f"⚠️ Файл слишком мал: {url}")
                
                # Метод 2: Через браузерный бот
                if hasattr(self.monitor, 'download_with_browser_bot'):
                    result = self.monitor.download_with_browser_bot(url, save_path)
                    if result in ['new', 'updated']:
                        self.update_file_records(url, save_path)
                        return True
                
            except Exception as e:
                self.logger.debug(f"🔄 Попытка {attempt + 1} неудачна: {e}")
        
        return False
    
    def update_file_records(self, url, save_path):
        """Обновление записей о скачанном файле"""
        try:
            with open(save_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            file_size = os.path.getsize(save_path)
            
            # Обновляем downloaded_files
            self.monitor.downloaded_files[url] = {
                'hash': file_hash,
                'path': save_path,
                'downloaded_at': datetime.now().isoformat(),
                'size': file_size,
                'method': 'unified_monitor'
            }
            
            # Обновляем discovered_files
            if url in self.monitor.discovered_files['files']:
                self.monitor.discovered_files['files'][url]['downloaded'] = True
                self.monitor.discovered_files['files'][url]['last_downloaded'] = datetime.now().isoformat()
                self.monitor.discovered_files['files'][url]['is_new'] = False
            
            # Сохраняем
            self.monitor.save_downloaded_history()
            self.monitor.save_discovered_files()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка обновления записей: {e}")
    
    def organize_files_automatically(self):
        """Автоматическая организация файлов по папкам"""
        try:
            moved_files = 0
            
            for url, file_info in self.monitor.discovered_files.get('files', {}).items():
                if not file_info.get('downloaded', False):
                    continue
                
                if url not in self.monitor.downloaded_files:
                    continue
                
                current_path = self.monitor.downloaded_files[url].get('path')
                if not current_path or not os.path.exists(current_path):
                    continue
                
                # Определяем правильный путь
                correct_dir = self.monitor.create_aifc_directory_structure(url, self.monitor.config['download_dir'])
                correct_filename = self.monitor.get_clean_filename(url)
                correct_path = os.path.join(correct_dir, correct_filename)
                
                # Если файл уже в правильном месте
                if os.path.normpath(current_path) == os.path.normpath(correct_path):
                    continue
                
                # Перемещаем файл
                try:
                    os.makedirs(correct_dir, exist_ok=True)
                    shutil.move(current_path, correct_path)
                    
                    # Обновляем путь в базе
                    self.monitor.downloaded_files[url]['path'] = correct_path
                    moved_files += 1
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Не удалось переместить {os.path.basename(current_path)}: {e}")
            
            if moved_files > 0:
                self.logger.info(f"📁 Перемещено файлов: {moved_files}")
                self.monitor.save_downloaded_history()
            else:
                self.logger.info("📁 Все файлы уже организованы правильно")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка организации файлов: {e}")
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        end_time = datetime.now()
        duration = end_time - self.session_report['start_time']
        
        self.session_report.update({
            'end_time': end_time,
            'duration_seconds': duration.total_seconds(),
            'duration_formatted': str(duration).split('.')[0]
        })
        
        report = f"""
🏁 ФИНАЛЬНЫЙ ОТЧЕТ АВТОМАТИЧЕСКОГО МОНИТОРИНГА AIFC
{'=' * 60}

⏰ ВРЕМЯ ВЫПОЛНЕНИЯ:
   Начало: {self.session_report['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
   Конец:  {self.session_report['end_time'].strftime('%Y-%m-%d %H:%M:%S')}
   Продолжительность: {self.session_report['duration_formatted']}

📊 СТАТИСТИКА:
   📄 Всего файлов в базе: {self.session_report['discovered_files']}
   📥 Скачано в этой сессии: {self.session_report['total_downloaded']}
   ❌ Ошибок скачивания: {self.session_report['download_errors']}

📁 РЕЗУЛЬТАТ:
   ✅ Все файлы организованы в: {self.monitor.config['download_dir']}
   📋 Структура папок создана автоматически
   💾 База данных обновлена

"""
        
        if self.session_report['errors']:
            report += f"❌ ОШИБКИ ({len(self.session_report['errors'])}):\n"
            for i, error in enumerate(self.session_report['errors'], 1):
                report += f"   {i}. {error}\n"
        
        report += f"""
{'=' * 60}
🎉 МОНИТОРИНГ ЗАВЕРШЕН!
"""
        
        self.logger.info(report)
        
        # Сохраняем отчет в файл
        report_filename = f"aifc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return self.session_report
    
    def generate_error_report(self, critical_error):
        """Генерация отчета об ошибке"""
        report = f"""
❌ КРИТИЧЕСКАЯ ОШИБКА В МОНИТОРИНГЕ
{'=' * 50}

⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🚨 Ошибка: {critical_error}

📊 Статистика до ошибки:
   📄 Файлов обнаружено: {self.session_report.get('discovered_files', 0)}
   📥 Файлов скачано: {self.session_report.get('total_downloaded', 0)}
"""
        
        self.logger.error(report)
        return {'error': str(critical_error), 'report': report}

def show_banner():
    """Баннер программы"""
    print("🏛️ ЕДИНЫЙ AIFC COURT DOCUMENT MONITOR")
    print("=" * 50)
    print("Полностью автоматизированный мониторинг документов")
    print(f"Версия: 3.0 Unified | {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 50)

def main():
    """Главная функция"""
    show_banner()
    
    print("\n🚀 РЕЖИМЫ РАБОТЫ:")
    print("1. Автоматический мониторинг (рекомендуется)")
    print("2. Быстрый анализ (без скачивания)")
    print("3. Выход")
    
    choice = input("\nВыберите режим (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 ЗАПУСК АВТОМАТИЧЕСКОГО МОНИТОРИНГА")
        print("=" * 45)
        print("Программа автоматически:")
        print("✅ Проверит локальную базу данных")
        print("✅ Найдет недостающие файлы")
        print("✅ Проверит сайт на новые документы")
        print("✅ Скачает новые и недостающие файлы")
        print("✅ Организует файлы по папкам")
        print("✅ Создаст подробный отчет")
        
        confirm = input("\n🚀 Начать? (да/нет): ").lower()
        
        if confirm in ['да', 'yes', 'y']:
            try:
                monitor = UnifiedAIFCMonitor()
                results = monitor.run_full_automation()
                
                if 'error' not in results:
                    print(f"\n🎉 МОНИТОРИНГ ЗАВЕРШЕН УСПЕШНО!")
                    print(f"📥 Скачано файлов: {results.get('total_downloaded', 0)}")
                    print(f"⏱️ Время: {results.get('duration_formatted', 'unknown')}")
                    print(f"📁 Файлы в: aifc_documents/")
                else:
                    print(f"\n❌ ЗАВЕРШЕН С ОШИБКОЙ: {results['error']}")
                    
            except Exception as e:
                print(f"\n❌ Критическая ошибка: {e}")
        else:
            print("❌ Отменено")
    
    elif choice == "2":
        print("\n📊 БЫСТРЫЙ АНАЛИЗ")
        print("=" * 25)
        
        try:
            monitor = UnifiedAIFCMonitor()
            
            # Анализ локальной базы
            local_status = monitor.analyze_local_database()
            
            # Анализ файлов на диске
            file_status = monitor.analyze_and_fix_file_records()
            
            # Подсчет файлов для скачивания
            files_to_download = monitor.get_files_to_download()
            
            print(f"\n📋 РЕЗУЛЬТАТЫ АНАЛИЗА:")
            print(f"📄 Всего файлов в базе: {local_status.get('discovered_count', 0)}")
            
            if files_to_download:
                print(f"📥 Нужно скачать: {len(files_to_download)} файлов")
                print("💡 Запустите автоматический режим для скачивания")
            else:
                print("✅ Все файлы уже скачаны!")
                
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
    
    elif choice == "3":
        print("👋 До свидания!")
    
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    import random  # Для задержек
    main()
