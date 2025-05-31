# Заменить импорт
try:
    from enhanced_browser_bot import SuperHumanBrowserBot as AdvancedBrowserBot
except ImportError:
    from browser_bot import AdvancedBrowserBot
import os
import requests
import time
import json
import hashlib
import re
import random
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from pathlib import Path
import logging
from datetime import datetime, timedelta
import schedule

class HumanLikeDocumentMonitor:
    def __init__(self, config_file='monitor_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.downloaded_files = self.load_downloaded_history()
        self.discovered_files = self.load_discovered_files()
        self.session = requests.Session()
        self.setup_human_like_session()
        self.initial_scan_completed = self.check_initial_scan_status()
        self.is_first_run = self.check_if_first_run()
        self.browser_bot = None
        
    def get_browser_bot(self):
        """Получить экземпляр браузерного бота (ленивая инициализация)"""
        if self.browser_bot is None:
            try:
                from browser_bot import AdvancedBrowserBot
                # Запускаем в headless режиме для продакшна, с GUI для отладки
                headless_mode = self.config.get('browser_headless', True)
                self.browser_bot = AdvancedBrowserBot(
                    headless=headless_mode, 
                    stealth_mode=True
                )
                self.logger.info("🤖 Браузерный бот инициализирован")
            except ImportError:
                self.logger.warning("⚠️ Браузерный бот недоступен. Установите: pip install selenium undetected-chromedriver")
                self.browser_bot = None
            except Exception as e:
                self.logger.error(f"❌ Ошибка инициализации браузерного бота: {e}")
                self.browser_bot = None
        
        return self.browser_bot
    
    def check_if_first_run(self):
        """Проверка первого запуска программы"""
        first_run_file = 'first_run_completed.json'
        try:
            with open(first_run_file, 'r') as f:
                data = json.load(f)
                is_first = not data.get('completed', False)
                if is_first:
                    self.logger.info("🆕 Это первый запуск программы")
                else:
                    self.logger.debug("Программа уже запускалась ранее")
                return is_first
        except FileNotFoundError:
            self.logger.info("🆕 Файл первого запуска не найден - это первый запуск")
            return True
    
    def mark_first_run_completed(self):
        """Отметить первый запуск как завершенный"""
        first_run_file = 'first_run_completed.json'
        with open(first_run_file, 'w') as f:
            json.dump({
                'completed': True,
                'completed_at': datetime.now().isoformat()
            }, f, indent=2)
        self.is_first_run = False
    
    def is_working_hours(self):
        """Проверка рабочих часов (9:00-18:00, пн-пт)"""
        now = datetime.now()
        
        # Проверяем день недели (0=понедельник, 6=воскресенье)
        if now.weekday() >= 5:  # суббота или воскресенье
            self.logger.debug(f"Выходной день: {now.strftime('%A')}")
            return False
        
        # Проверяем время (9:00-18:00)
        hour = now.hour
        is_work_time = 9 <= hour < 18
        
        if not is_work_time:
            self.logger.debug(f"Нерабочее время: {hour}:00 (работаем 9:00-18:00)")
        
        return is_work_time
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        default_config = {
            "urls": [
                "https://court.aifc.kz/en/judgments",
                "https://court.aifc.kz/en/legislation"
            ],
            "download_dir": "aifc_documents",
            "check_interval_minutes": 120,
            "file_extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".zip", ".rar"],
            "max_depth": 3,
            "timeout": 30,
            "browser_enabled": True,
            "browser_headless": True,
            "browser_fallback": True,
            "max_filename_length": 150,
            "human_behavior": {
                "browsing_probability": 0.7,
                "min_session_time": 120,
                "max_session_time": 600,
                "pages_per_session": [3, 8],
                "interval_variation": 0.3,
                "short_break_probability": 0.05,
                "long_break_probability": 0.05,
                "mini_visit_probability": 0.001,
                "initial_scan_days": 15,
                "monitoring_cycle_days_min": 7,
                "monitoring_cycle_days_max": 10,
                "working_hours_start": 9,
                "working_hours_end": 18,
                "working_days": [0, 1, 2, 3, 4],
                "first_run_always_download": True,
                "initial_download_probability_min": 0.5,
                "initial_download_probability_max": 0.8,
                "monitoring_download_probability_min": 0.15,
                "monitoring_download_probability_max": 0.45
            }
        }
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"Создан файл конфигурации: {self.config_file}")
            return default_config
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('document_monitor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_downloaded_history(self):
        """Загрузка истории скачанных файлов"""
        try:
            with open('downloaded_files.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_downloaded_history(self):
        """Сохранение истории скачанных файлов"""
        with open('downloaded_files.json', 'w', encoding='utf-8') as f:
            json.dump(self.downloaded_files, f, indent=2, ensure_ascii=False)
    
    def load_discovered_files(self):
        """Загрузка списка всех обнаруженных файлов"""
        try:
            with open('discovered_files.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'files': {},
                'last_full_scan': None,
                'initial_scan_completed': False,
                'scan_start_date': datetime.now().isoformat()
            }
    
    def save_discovered_files(self):
        """Сохранение списка обнаруженных файлов"""
        with open('discovered_files.json', 'w', encoding='utf-8') as f:
            json.dump(self.discovered_files, f, indent=2, ensure_ascii=False)
    
    def check_initial_scan_status(self):
        """Проверка статуса первоначального сканирования"""
        # Упрощенная версия - всегда возвращаем False для демо
        return False
    
    def setup_human_like_session(self):
        """Настройка сессии для имитации реального пользователя"""
        # Ротация User-Agent'ов
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36'
        ]
        
        # Настройка заголовков как у реального браузера
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0'
        })
    
    def get_random_user_agent(self):
        """Получить случайный User-Agent"""
        return random.choice(self.user_agents)
    
    def human_delay(self, min_seconds=2, max_seconds=8):
        """Человеческая задержка между действиями"""
        delay = random.uniform(min_seconds, max_seconds)
        self.logger.debug(f"Пауза {delay:.1f} секунд...")
        time.sleep(delay)
    
    def should_download_now(self):
        """Решает, стоит ли скачивать документы сейчас (адаптивно)"""
        
        # Первый запуск - всегда скачиваем ВСЕ документы
        if self.is_first_run:
            self.logger.info("🚀 Первый запуск - скачиваем ВСЕ документы!")
            return True
        
        # Обычный мониторинг - проверяем рабочие часы
        if not self.is_working_hours():
            self.logger.info("💤 Нерабочее время - только браузинг")
            return False
        
        # В рабочие часы всегда проверяем на новые/измененные документы
        self.logger.info("🔍 Режим мониторинга - проверяем новые и измененные документы")
        return True
    
    def crawl_with_browser_bot(self, url):
        """Обход сайта с помощью браузерного бота"""
        bot = self.get_browser_bot()
        if not bot:
            self.logger.warning("🔄 Браузерный бот недоступен, используем обычный метод")
            return []
        
        try:
            self.logger.info(f"🤖 Используем браузерный бот для: {url}")
            
            # Имитируем человеческое поведение
            bot.simulate_human_browsing("https://court.aifc.kz")
            
            # Переходим на целевую страницу
            if bot.visit_page_like_human(url):
                
                # Ищем документы
                documents = bot.find_document_links()
                
                # Преобразуем в нужный формат
                document_urls = []
                for doc in documents:
                    document_urls.append(doc['url'])
                    self.logger.info(f"🔗 Найден браузером: {doc['url']}")
                
                return document_urls
            else:
                self.logger.warning(f"❌ Не удалось загрузить страницу в браузере: {url}")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка работы браузерного бота: {e}")
            return []
    
    def create_aifc_directory_structure(self, url, base_dir):
        """Создание структуры папок специально для AIFC Court с улучшенной классификацией"""
        parsed_url = urlparse(url)
        url_lower = url.lower()
        
        # Подробная классификация документов
        folder_name = 'Other_Documents'  # По умолчанию
        
        # Судебные решения и дела
        if any(keyword in url_lower for keyword in [
            'judgments', '/uploads/', 'case%20no', 'judgment', 
            'case_no', 'case-no', 'decision', 'ruling'
        ]):
            folder_name = 'Judgments'
            self.logger.debug(f"📂 Классифицировано как судебное решение: {url}")
        
        # Законодательство и правила
        elif any(keyword in url_lower for keyword in [
            'legislation', '/legals/', 'regulations', 'rules', 
            'policy', 'consultation-paper', 'guidance', 'notice',
            'amendment', 'circular', 'directive', 'order'
        ]):
            folder_name = 'Legislation'
            self.logger.debug(f"📂 Классифицировано как законодательство: {url}")
        
        # Если содержит специфические ключевые слова AIFC
        elif any(keyword in url_lower for keyword in [
            'aifc-court-regulations', 'aifc-court-rules', 
            'template-of-offering', 'afsa-policy'
        ]):
            folder_name = 'Legislation'
            self.logger.debug(f"📂 Классифицировано как AIFC законодательство: {url}")
        
        else:
            self.logger.debug(f"📂 Классифицировано как прочие документы: {url}")
        
        # Создаем основную структуру
        full_path = os.path.join(base_dir, 'AIFC_Court', folder_name)
        
        # Для решений судов создаем подпапки по годам
        if folder_name == 'Judgments':
            year_match = re.search(r'20\d{2}', url)
            if year_match:
                year = year_match.group()
                full_path = os.path.join(full_path, year)
                self.logger.debug(f"📅 Создана подпапка для года: {year}")
        
        # Для законодательства можно создать подпапки по типу
        elif folder_name == 'Legislation':
            if 'consultation-paper' in url_lower:
                full_path = os.path.join(full_path, 'Consultation_Papers')
            elif 'guidance' in url_lower:
                full_path = os.path.join(full_path, 'Guidance_Documents')
            elif 'notice' in url_lower:
                full_path = os.path.join(full_path, 'Notices')
            elif 'template' in url_lower:
                full_path = os.path.join(full_path, 'Templates')
        
        # Включаем поддержку длинных путей в Windows
        if os.name == 'nt':  # Windows
            if not full_path.startswith('\\\\?\\'):
                full_path = '\\\\?\\' + os.path.abspath(full_path)
        
        try:
            os.makedirs(full_path, exist_ok=True)
        except OSError as e:
            if "path too long" in str(e).lower() or e.errno == 2:
                # Fallback: создаем более короткий путь
                self.logger.warning(f"⚠️ Путь слишком длинный, создаем сокращенную версию")
                short_path = os.path.join(base_dir, 'AIFC_Court', folder_name[:20])
                os.makedirs(short_path, exist_ok=True)
                return short_path
            else:
                raise
        
        return full_path
    
    def get_clean_filename(self, url, content_disposition=None):
        """Получение чистого имени файла с обработкой длинных имен"""
        max_length = self.config.get('max_filename_length', 150)
        
        if content_disposition:
            filename_match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', content_disposition)
            if filename_match:
                filename = filename_match.group(1).strip()
                if filename:
                    filename = unquote(filename)
        else:
            parsed_url = urlparse(url)
            filename = os.path.basename(unquote(parsed_url.path))
        
        if 'court.aifc.kz' in url:
            if filename:
                filename = filename.replace('%20', ' ')
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                if '.' not in filename and '/uploads/' in url:
                    filename += '.pdf'
        
        # Обработка слишком длинных имен файлов
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            
            # Создаем сокращенную версию
            if len(name) > max_length - len(ext) - 10:  # Оставляем место для расширения и хеша
                # Берем первые слова + хеш URL для уникальности
                words = name.split('-')
                short_name = '-'.join(words[:3])  # Первые 3 слова
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                
                # Ограничиваем длину
                available_length = max_length - len(ext) - len(url_hash) - 1
                if len(short_name) > available_length:
                    short_name = short_name[:available_length]
                
                filename = f"{short_name}_{url_hash}{ext}"
                
                self.logger.info(f"📝 Сокращено длинное имя файла:")
                self.logger.info(f"   Исходное: {name[:50]}...")
                self.logger.info(f"   Новое: {filename}")
        
        # Финальная проверка
        if not filename or '.' not in filename:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            if 'judgments' in url.lower():
                filename = f"judgment_{url_hash}.pdf"
            elif 'legislation' in url.lower() or 'legals' in url.lower():
                filename = f"legislation_{url_hash}.pdf"
            else:
                filename = f"document_{url_hash}.pdf"
        
        return filename
    
    def update_discovered_files(self, documents):
        """Обновление списка обнаруженных файлов"""
        current_time = datetime.now().isoformat()
        
        for doc_url in documents:
            if doc_url not in self.discovered_files['files']:
                self.discovered_files['files'][doc_url] = {
                    'first_seen': current_time,
                    'last_seen': current_time,
                    'downloaded': False,
                    'is_new': True  # Помечаем как новый
                }
                self.logger.info(f"🆕 Обнаружен новый документ: {doc_url}")
            else:
                self.discovered_files['files'][doc_url]['last_seen'] = current_time
                # Если файл уже был, но не скачан - тоже считаем новым
                if not self.discovered_files['files'][doc_url].get('downloaded', False):
                    self.discovered_files['files'][doc_url]['is_new'] = True
        
        self.discovered_files['last_full_scan'] = current_time
        self.save_discovered_files()
    
    def get_files_to_download(self, documents):
        """Определить какие файлы нужно скачать"""
        if self.is_first_run:
            # Первый запуск - скачиваем ВСЕ документы
            self.logger.info(f"📋 Первый запуск: планируем скачать ВСЕ {len(documents)} документов")
            return documents
        
        # Режим мониторинга - только новые и измененные
        files_to_download = []
        
        for doc_url in documents:
            file_info = self.discovered_files['files'].get(doc_url, {})
            
            # Новый файл
            if file_info.get('is_new', False):
                files_to_download.append(doc_url)
                self.logger.info(f"🆕 К скачиванию: новый файл {doc_url}")
            
            # Файл не был скачан ранее
            elif not file_info.get('downloaded', False):
                files_to_download.append(doc_url)
                self.logger.info(f"📥 К скачиванию: не скачанный файл {doc_url}")
            
            # Проверяем на изменения уже скачанные файлы
            elif doc_url in self.downloaded_files:
                files_to_download.append(doc_url)
                self.logger.debug(f"🔄 К проверке на изменения: {doc_url}")
        
        self.logger.info(f"📊 К обработке: {len(files_to_download)} из {len(documents)} файлов")
        return files_to_download
    
    def get_file_hash(self, content):
        """Получение хеша файла для проверки изменений"""
        return hashlib.md5(content).hexdigest()
    
    def download_with_browser_bot(self, url, save_path):
        """Скачивание файла через браузерный бот с проверкой изменений"""
        bot = self.get_browser_bot()
        if not bot:
            return self.download_file_simple(url, save_path)
        
        try:
            # Проверяем нужно ли перезаписывать файл
            file_exists = os.path.exists(save_path)
            old_hash = None
            
            if file_exists and url in self.downloaded_files:
                old_hash = self.downloaded_files[url]['hash']
            
            # Используем браузер для получения файла
            if bot.visit_page_like_human(url):
                
                # Получаем куки из браузера
                cookies = bot.driver.get_cookies()
                session_cookies = {}
                for cookie in cookies:
                    session_cookies[cookie['name']] = cookie['value']
                
                # Скачиваем через requests с куками браузера
                headers = {
                    'User-Agent': bot.driver.execute_script("return navigator.userAgent;"),
                    'Referer': bot.driver.current_url
                }
                
                response = self.session.get(url, headers=headers, cookies=session_cookies, stream=True)
                response.raise_for_status()
                
                file_content = response.content
                file_hash = self.get_file_hash(file_content)
                
                # Проверяем изменения
                if old_hash and old_hash == file_hash:
                    self.logger.debug(f"⚪ Файл не изменился: {os.path.basename(save_path)}")
                    return "unchanged"
                
                # Создаем резервную копию если файл изменился
                if file_exists and old_hash and old_hash != file_hash:
                    backup_path = save_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    import shutil
                    shutil.copy2(save_path, backup_path)
                    self.logger.info(f"🔄 Файл изменился! Создана резервная копия: {os.path.basename(backup_path)}")
                
                # Сохраняем новый файл
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(file_content)
                
                # Обновляем метаданные
                self.downloaded_files[url] = {
                    'hash': file_hash,
                    'path': save_path,
                    'downloaded_at': datetime.now().isoformat(),
                    'size': len(file_content),
                    'method': 'browser_bot'
                }
                
                # Помечаем файл как скачанный
                if url in self.discovered_files['files']:
                    self.discovered_files['files'][url]['downloaded'] = True
                    self.discovered_files['files'][url]['last_downloaded'] = datetime.now().isoformat()
                    self.discovered_files['files'][url]['is_new'] = False
                
                if file_exists and old_hash != file_hash:
                    self.logger.info(f"🔄📄 Обновлен файл: {os.path.basename(save_path)} ({len(file_content)} байт)")
                    return "updated"
                else:
                    self.logger.info(f"🆕📄 Скачан новый файл: {os.path.basename(save_path)} ({len(file_content)} байт)")
                    return "new"
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка скачивания через браузер {url}: {e}")
            # Fallback на обычный метод
            return self.download_file_simple(url, save_path)
        
        return "failed"
    
    def download_file_simple(self, url, save_path):
        """Простое скачивание файла через requests"""
        try:
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'application/pdf,application/vnd.ms-excel,*/*',
            }
            
            response = self.session.get(url, headers=headers, timeout=self.config['timeout'], stream=True)
            response.raise_for_status()
            
            file_content = response.content
            file_hash = self.get_file_hash(file_content)
            
            if url in self.downloaded_files and self.downloaded_files[url]['hash'] == file_hash:
                self.logger.debug(f"Файл не изменился: {url}")
                return "unchanged"
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(file_content)
            
            self.downloaded_files[url] = {
                'hash': file_hash,
                'path': save_path,
                'downloaded_at': datetime.now().isoformat(),
                'size': len(file_content),
                'method': 'requests'
            }
            
            self.logger.info(f"📄 Скачан файл: {save_path} ({len(file_content)} байт)")
            return "new"
            
        except Exception as e:
            self.logger.error(f"Ошибка при скачивании {url}: {str(e)}")
            return "failed"
    
    def human_like_session(self):
        """Проведение человекоподобной сессии на сайте"""
        base_url = "https://court.aifc.kz"
        
        self.logger.info("🚀 Начинаем новую сессию на сайте...")
        
        # Показываем время и статус рабочих часов
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        day_str = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][now.weekday()]
        
        if self.is_first_run:
            self.logger.info(f"🕐 {day_str} {time_str} - Первый запуск программы")
        elif self.is_working_hours():
            self.logger.info(f"🕐 {day_str} {time_str} - Рабочие часы")
        else:
            self.logger.info(f"🕐 {day_str} {time_str} - Нерабочее время")
        
        # Определяем, что будем делать в этой сессии
        will_download = self.should_download_now()
        
        if will_download:
            self.logger.info("📋 Планируем скачать документы в этой сессии")
        else:
            self.logger.info("👀 Просто изучаем сайт в этой сессии")
        
        if will_download:
            # Переходим к скачиванию документов
            if self.is_first_run:
                self.logger.info("📥 ПЕРВЫЙ ЗАПУСК: Скачиваем ВСЕ документы с сайта...")
            else:
                self.logger.info("📥 МОНИТОРИНГ: Проверяем новые и измененные документы...")
            
            total_new = 0
            total_updated = 0
            total_unchanged = 0
            total_failed = 0
            
            for url in self.config['urls']:
                self.human_delay(3, 8)
                
                # Используем браузерный бот если доступен
                documents = self.crawl_with_browser_bot(url)
                
                self.logger.info(f"📊 Найдено документов на {url}: {len(documents)}")
                
                if documents:
                    # Обновляем список обнаруженных файлов
                    self.update_discovered_files(documents)
                    
                    # Определяем какие файлы нужно скачать
                    files_to_download = self.get_files_to_download(documents)
                    
                    if files_to_download:
                        self.logger.info(f"🎯 К обработке: {len(files_to_download)} файлов")
                        
                        for i, doc_url in enumerate(files_to_download):
                            try:
                                # Показываем прогресс
                                self.logger.info(f"📥 [{i+1}/{len(files_to_download)}] Обрабатываем: {os.path.basename(doc_url)}")
                                
                                self.human_delay(1, 3)  # Уменьшенная задержка для массового скачивания
                                
                                save_dir = self.create_aifc_directory_structure(doc_url, self.config['download_dir'])
                                filename = self.get_clean_filename(doc_url)
                                save_path = os.path.join(save_dir, filename)
                                
                                result = self.download_with_browser_bot(doc_url, save_path)
                                
                                if result == "new":
                                    total_new += 1
                                elif result == "updated":
                                    total_updated += 1
                                elif result == "unchanged":
                                    total_unchanged += 1
                                else:
                                    total_failed += 1
                                
                                # Периодически сохраняем прогресс
                                if (i + 1) % 5 == 0:
                                    self.save_downloaded_history()
                                    self.save_discovered_files()
                                    self.logger.info(f"💾 Прогресс сохранен ({i+1}/{len(files_to_download)})")
                                    
                            except Exception as e:
                                self.logger.error(f"Ошибка при обработке {doc_url}: {str(e)}")
                                total_failed += 1
                    else:
                        self.logger.info("📂 Новых файлов для скачивания не найдено")
                else:
                    self.logger.warning(f"⚠️ Документы не найдены на {url}")
        
            # Итоговая статистика
            self.print_download_statistics(total_new, total_updated, total_unchanged, total_failed)
            
            # Отмечаем первый запуск как завершенный
            if self.is_first_run:
                self.mark_first_run_completed()
                self.logger.info("🎉 Первый запуск завершен! Все документы скачаны.")
                self.logger.info("🔄 Следующие запуски будут только отслеживать изменения.")
        
        self.logger.info("🏁 Завершаем сессию")
        
        # Сохраняем финальные данные
        self.save_downloaded_history()
        self.save_discovered_files()
        
        # Закрываем браузерный бот
        if self.browser_bot:
            try:
                self.browser_bot.close()
                self.browser_bot = None
                self.logger.info("🔒 Браузерный бот закрыт")
            except Exception as e:
                self.logger.error(f"Ошибка закрытия браузерного бота: {e}")
    
    def print_download_statistics(self, new, updated, unchanged, failed):
        """Вывод статистики скачивания"""
        total = new + updated + unchanged + failed
        
        if self.is_first_run:
            self.logger.info("🎯 Режим: Первоначальное скачивание завершено!")
        else:
            self.logger.info("🔍 Режим: Мониторинг изменений")
            
        self.logger.info("=" * 50)
        self.logger.info("📊 СТАТИСТИКА СЕССИИ:")
        self.logger.info(f"🆕 Новых файлов: {new}")
        self.logger.info(f"🔄 Обновленных файлов: {updated}")
        self.logger.info(f"⚪ Без изменений: {unchanged}")
        if failed > 0:
            self.logger.info(f"❌ Ошибок: {failed}")
        self.logger.info(f"📁 Всего обработано: {total}")
        
    def generate_session_report(self):
        """Генерация краткого отчета о сессии"""
        try:
            from report_generator import ReportGenerator
            
            generator = ReportGenerator(self.config['download_dir'])
            
            # Быстрая статистика
            downloaded_files, discovered_files, first_run_data = generator.load_data()
            structure, total_size, total_files = generator.analyze_file_structure()
            
            self.logger.info("📊 КРАТКИЙ ОТЧЕТ:")
            self.logger.info(f"   📁 Всего файлов: {total_files}")
            self.logger.info(f"   💾 Общий размер: {generator.format_size(total_size)}")
            self.logger.info(f"   🔗 В базе данных: {len(downloaded_files)} записей")
            
        except ImportError:
            self.logger.debug("Модуль отчетов недоступен")
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
    
    def generate_full_report(self):
        """Генерация полного отчета"""
        try:
            from report_generator import ReportGenerator
            
            self.logger.info("📋 Генерируем полный отчет...")
            generator = ReportGenerator(self.config['download_dir'])
            
            # Генерируем консольный отчет
            generator.generate_console_report()
            
            # Генерируем JSON отчет
            json_file = generator.generate_json_report()
            self.logger.info(f"💾 Детальный отчет сохранен: {json_file}")
            
        except ImportError:
            self.logger.warning("⚠️ Модуль отчетов недоступен")
        except Exception as e:
            self.logger.error(f"Ошибка генерации полного отчета: {e}")

    def retry_failed_downloads(self):
        """Повторная попытка скачивания неудачных файлов"""
        self.logger.info("🔄 Проверяем файлы для повторного скачивания...")
        
        retry_count = 0
        for url, file_info in self.discovered_files['files'].items():
            if not file_info.get('downloaded', False):
                try:
                    self.logger.info(f"🔄 Повторная попытка: {os.path.basename(url)}")
                    
                    save_dir = self.create_aifc_directory_structure(url, self.config['download_dir'])
                    filename = self.get_clean_filename(url)
                    save_path = os.path.join(save_dir, filename)
                    
                    result = self.download_with_browser_bot(url, save_path)
                    
                    if result in ["new", "updated"]:
                        retry_count += 1
                        self.logger.info(f"✅ Успешно скачан при повторной попытке: {filename}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Повторная попытка неудачна для {url}: {e}")
        
        if retry_count > 0:
            self.logger.info(f"🎉 Успешно скачано при повторных попытках: {retry_count} файлов")
            self.save_downloaded_history()
            self.save_discovered_files()
        else:
            self.logger.info("📂 Нет файлов для повторного скачивания")

    def test_classification_logic(self):
        """Тестовая функция для проверки классификации"""
        test_urls = [
            "https://court.aifc.kz/files/legals/543/file/template-of-offering-materials-for-exempt-fund.pdf",
            "https://court.aifc.kz/files/legals/544/file/template-of-offering-materials-for-non-exempt-fund.pdf",
            "https://court.aifc.kz/uploads/judgments/case_no_1_2019.pdf",
            "https://court.aifc.kz/files/legals/577/file/guidance-on-spr-rus.pdf",
            "https://court.aifc.kz/files/legals/597/file/aifc-amlcft-practical-guidance_03-11-2023.pdf"
        ]
        
        print("🧪 Тестирование классификации:")
        for url in test_urls:
            path = self.create_aifc_directory_structure(url, "test_dir")
            print(f"URL: {url}")
            print(f"Path: {path}")
            print("-" * 50)

# Алиас для обратной совместимости
DocumentMonitor = HumanLikeDocumentMonitor

def enable_long_paths_windows():
    """Включение поддержки длинных путей в Windows (требует admin прав)"""
    import subprocess
    import sys
    
    if os.name == 'nt':
        try:
            # Попытка включить длинные пути через реестр
            cmd = [
                'reg', 'add', 
                'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\FileSystem',
                '/v', 'LongPathsEnabled', '/t', 'REG_DWORD', '/d', '1', '/f'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Длинные пути включены в реестре Windows")
                print("⚠️ Требуется перезагрузка для применения изменений")
                return True
            else:
                print("❌ Не удалось включить длинные пути (нужны права администратора)")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при попытке включить длинные пути: {e}")
            return False
    
    return True

def main():
    """Главная функция"""
    print("🤖 Человекоподобный монитор документов AIFC Court")
    print("=" * 50)
    
    # Попытка включить длинные пути в Windows
    if os.name == 'nt':
        print("🔧 Проверяем поддержку длинных путей в Windows...")
        enable_long_paths_windows()
    
    monitor = HumanLikeDocumentMonitor()
    
    if not monitor.config['urls']:
        print("⚠️ Не настроены URL для мониторинга!")
        print(f"Отредактируйте файл '{monitor.config_file}' и добавьте URL в секцию 'urls'")
        return
    
    print(f"🎯 Настроенные URL для мониторинга:")
    for url in monitor.config['urls']:
        print(f"  • {url}")
    
    print(f"\n📁 Папка сохранения: {monitor.config['download_dir']}")
    print(f"🎭 Режим: Имитация реального пользователя с браузерным ботом")
    print(f"📏 Максимальная длина имени файла: {monitor.config.get('max_filename_length', 150)} символов")
    
    monitor.human_like_session()

if __name__ == "__main__":
    main()
