"""
Продвинутый браузерный бот с усиленной имитацией человеческого поведения
"""

import time
import random
import json
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
from urllib.parse import urlparse, urljoin
import os

class SuperHumanBrowserBot:
    def __init__(self, headless=False, stealth_mode=True, ultra_stealth=True):
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.ultra_stealth = ultra_stealth
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.session_cookies = {}
        self.human_behavior_patterns = self.init_human_patterns()
        self.setup_driver()
        
    def init_human_patterns(self):
        """Инициализация паттернов человеческого поведения"""
        return {
            'reading_speed': (2, 8),  # секунды на чтение страницы
            'scroll_patterns': [
                'slow_careful',    # медленное внимательное чтение
                'quick_scan',      # быстрое сканирование
                'detailed_study',  # детальное изучение
                'random_browse'    # случайное брожение
            ],
            'break_probability': 0.15,  # вероятность паузы
            'long_break_duration': (30, 120),  # длинная пауза
            'short_break_duration': (5, 15),   # короткая пауза
            'retry_delays': [10, 30, 60, 120, 300],  # задержки при повторах
        }
    
    def setup_driver(self):
        """Настройка максимально стелс браузера"""
        try:
            if self.ultra_stealth:
                # Используем самую продвинутую стелс-конфигурацию
                options = uc.ChromeOptions()
                
                # Базовые стелс-опции
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-web-security')
                options.add_argument('--allow-running-insecure-content')
                options.add_argument('--disable-features=VizDisplayCompositor')
                
                # Продвинутые антидетект опции
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-automation')
                options.add_argument('--disable-infobars')
                options.add_argument('--disable-plugins-discovery')
                options.add_argument('--disable-default-apps')
                options.add_argument('--disable-background-timer-throttling')
                options.add_argument('--disable-backgrounding-occluded-windows')
                options.add_argument('--disable-renderer-backgrounding')
                options.add_argument('--disable-features=TranslateUI')
                
                # Имитация реального пользователя
                options.add_argument('--enable-features=NetworkService,NetworkServiceLogging')
                options.add_argument('--disable-ipc-flooding-protection')
                options.add_argument('--disable-client-side-phishing-detection')
                options.add_argument('--disable-sync')
                options.add_argument('--disable-component-extensions-with-background-pages')
                
                # Реалистичные настройки окна
                if not self.headless:
                    options.add_argument('--start-maximized')
                else:
                    options.add_argument('--headless=new')
                    options.add_argument('--window-size=1920,1080')
                
                # Продвинутые prefs
                prefs = {
                    "profile.default_content_setting_values": {
                        "notifications": 2,
                        "media_stream": 2,
                        "geolocation": 2,
                        "popups": 2
                    },
                    "profile.managed_default_content_settings": {
                        "images": 1
                    },
                    "profile.default_content_settings": {
                        "popups": 0
                    },
                    "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
                    "download.default_directory": os.getcwd(),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": False
                }
                options.add_experimental_option("prefs", prefs)
                
                # Исключаем автоматизацию из логов
                options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Создаем драйвер
                self.driver = uc.Chrome(
                    options=options,
                    version_main=None,
                    driver_executable_path=None
                )
                
                # Продвинутые JS-хаки для сокрытия автоматизации
                self.apply_stealth_scripts()
                
            else:
                # Обычная конфигурация как fallback
                options = Options()
                options.add_argument('--headless=new' if self.headless else '--start-maximized')
                self.driver = webdriver.Chrome(options=options)
            
            self.logger.info("✅ Супер-стелс браузер инициализирован")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации браузера: {e}")
            raise
    
    def apply_stealth_scripts(self):
        """Применение продвинутых скриптов для сокрытия автоматизации"""
        stealth_scripts = [
            # Удаляем webdriver property
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            
            # Подделываем permissions
            """
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({state: 'granted'})
                })
            });
            """,
            
            # Подделываем plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            """,
            
            # Подделываем languages
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'ru']
            });
            """,
            
            # Убираем следы Chrome Driver
            """
            window.chrome = {
                runtime: {
                    onConnect: undefined,
                    onMessage: undefined
                }
            };
            """,
            
            # Подделываем iframe проверки
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_script(script)
            except Exception as e:
                self.logger.debug(f"Не удалось выполнить стелс-скрипт: {e}")
    
    def human_like_delay(self, min_seconds=2, max_seconds=8, activity_type="normal"):
        """Продвинутые человеческие задержки в зависимости от активности"""
        if activity_type == "reading":
            delay = random.uniform(5, 15)  # Время на чтение
        elif activity_type == "downloading":
            delay = random.uniform(3, 8)   # Время на принятие решения о скачивании
        elif activity_type == "navigation":
            delay = random.uniform(1, 4)   # Время на навигацию
        elif activity_type == "scanning":
            delay = random.uniform(0.5, 2) # Быстрое сканирование
        else:
            delay = random.uniform(min_seconds, max_seconds)
        
        # Иногда делаем случайные паузы (имитация отвлечения)
        if random.random() < self.human_behavior_patterns['break_probability']:
            if random.random() < 0.3:  # Длинная пауза
                extra_delay = random.uniform(*self.human_behavior_patterns['long_break_duration'])
                self.logger.info(f"😴 Длинная пауза (имитация отвлечения): {extra_delay:.1f} сек")
            else:  # Короткая пауза
                extra_delay = random.uniform(*self.human_behavior_patterns['short_break_duration'])
                self.logger.debug(f"⏸ Короткая пауза: {extra_delay:.1f} сек")
            delay += extra_delay
        
        self.logger.debug(f"⏱ Человеческая задержка ({activity_type}): {delay:.1f} сек")
        time.sleep(delay)
    
    def realistic_scroll_behavior(self):
        """Реалистичное поведение скроллинга"""
        pattern = random.choice(self.human_behavior_patterns['scroll_patterns'])
        
        if pattern == 'slow_careful':
            # Медленное внимательное чтение
            for _ in range(random.randint(3, 7)):
                scroll_amount = random.randint(100, 300)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self.human_like_delay(2, 5, "reading")
                
        elif pattern == 'quick_scan':
            # Быстрое сканирование
            for _ in range(random.randint(5, 10)):
                scroll_amount = random.randint(200, 500)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self.human_like_delay(0.5, 2, "scanning")
                
        elif pattern == 'detailed_study':
            # Детальное изучение с возвратами
            for _ in range(random.randint(4, 8)):
                scroll_amount = random.randint(150, 400)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self.human_like_delay(3, 8, "reading")
                
                # Иногда возвращаемся назад для повторного чтения
                if random.random() < 0.3:
                    back_scroll = random.randint(50, 200)
                    self.driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
                    self.human_like_delay(2, 4, "reading")
                    
        elif pattern == 'random_browse':
            # Случайное брожение
            for _ in range(random.randint(3, 12)):
                if random.random() < 0.7:
                    scroll_amount = random.randint(100, 600)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                else:
                    scroll_amount = random.randint(100, 300)
                    self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
                self.human_like_delay(1, 4, "navigation")
    
    def visit_page_with_retry(self, url, max_retries=3):
        """Посещение страницы с умными повторами при блокировке"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🌐 Попытка {attempt + 1}/{max_retries}: {url}")
                
                # Если не первая попытка, делаем увеличивающуюся задержку
                if attempt > 0:
                    retry_delay = self.human_behavior_patterns['retry_delays'][min(attempt-1, 4)]
                    jittered_delay = retry_delay + random.uniform(-10, 30)
                    self.logger.info(f"⏳ Задержка перед повтором: {jittered_delay:.1f} сек")
                    time.sleep(jittered_delay)
                
                # Переходим на страницу
                self.driver.get(url)
                
                # Ждем загрузки
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Проверяем на блокировку
                page_title = self.driver.title.lower()
                page_source = self.driver.page_source.lower()
                
                blocking_indicators = [
                    'access denied', 'blocked', 'forbidden', 'captcha',
                    'too many requests', 'rate limit', 'bot detection',
                    'please wait', 'checking your browser'
                ]
                
                is_blocked = any(indicator in page_title or indicator in page_source 
                               for indicator in blocking_indicators)
                
                if is_blocked:
                    self.logger.warning(f"🚫 Обнаружена блокировка на попытке {attempt + 1}")
                    if attempt < max_retries - 1:
                        # Имитируем поведение заблокированного пользователя
                        self.simulate_blocked_user_behavior()
                        continue
                    else:
                        return False
                
                # Успешная загрузка - имитируем изучение страницы
                self.simulate_page_reading()
                return True
                
            except TimeoutException:
                self.logger.warning(f"⏰ Таймаут на попытке {attempt + 1}")
                if attempt == max_retries - 1:
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Ошибка на попытке {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return False
        
        return False
    
    def simulate_blocked_user_behavior(self):
        """Имитация поведения пользователя при блокировке"""
        self.logger.info("🤔 Имитируем поведение заблокированного пользователя...")
        
        # Пользователь обычно ждет, обновляет страницу, возможно переходит на главную
        behaviors = [
            'wait_and_refresh',
            'go_to_homepage',
            'close_and_reopen'
        ]
        
        behavior = random.choice(behaviors)
        
        if behavior == 'wait_and_refresh':
            self.human_like_delay(10, 30, "reading")  # Пользователь читает сообщение об ошибке
            self.driver.refresh()
            self.human_like_delay(5, 15, "reading")
            
        elif behavior == 'go_to_homepage':
            self.human_like_delay(5, 15, "reading")
            self.driver.get("https://court.aifc.kz")
            self.human_like_delay(10, 25, "reading")
            self.realistic_scroll_behavior()
            
        elif behavior == 'close_and_reopen':
            # Имитируем закрытие и повторное открытие (просто длинная пауза)
            self.human_like_delay(30, 90, "reading")
    
    def simulate_page_reading(self):
        """Имитация чтения страницы пользователем"""
        self.logger.debug("👀 Имитируем чтение страницы...")
        
        # Пользователь изучает заголовок
        self.human_like_delay(2, 5, "reading")
        
        # Скроллит и изучает контент
        self.realistic_scroll_behavior()
        
        # Возвращается наверх (частое поведение)
        if random.random() < 0.4:
            self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            self.human_like_delay(1, 3, "navigation")
    
    def smart_download_file(self, url, save_path, max_retries=5):
        """Умное скачивание файла с обходом блокировок"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"📥 Скачивание (попытка {attempt + 1}/{max_retries}): {os.path.basename(url)}")
                
                # Посещаем страницу с файлом
                if not self.visit_page_with_retry(url, max_retries=2):
                    self.logger.warning(f"❌ Не удалось загрузить страницу: {url}")
                    continue
                
                # Получаем куки из браузера для requests
                cookies = self.driver.get_cookies()
                session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                
                # Получаем заголовки браузера
                user_agent = self.driver.execute_script("return navigator.userAgent;")
                
                headers = {
                    'User-Agent': user_agent,
                    'Referer': self.driver.current_url,
                    'Accept': 'application/pdf,application/octet-stream,*/*',
                    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin'
                }
                
                # Пауза перед скачиванием (пользователь принимает решение)
                self.human_like_delay(2, 6, "downloading")
                
                # Скачиваем через requests с куками браузера
                response = requests.get(
                    url, 
                    headers=headers, 
                    cookies=session_cookies, 
                    stream=True,
                    timeout=30
                )
                
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_size = os.path.getsize(save_path)
                    self.logger.info(f"✅ Файл скачан: {os.path.basename(save_path)} ({file_size} байт)")
                    
                    # Небольшая пауза после успешного скачивания
                    self.human_like_delay(1, 3, "navigation")
                    return True
                    
                else:
                    self.logger.warning(f"⚠️ HTTP {response.status_code} для {url}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"🌐 Сетевая ошибка (попытка {attempt + 1}): {e}")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка скачивания (попытка {attempt + 1}): {e}")
            
            # Задержка перед следующей попыткой
            if attempt < max_retries - 1:
                retry_delay = self.human_behavior_patterns['retry_delays'][min(attempt, 4)]
                jittered_delay = retry_delay + random.uniform(-5, 15)
                self.logger.info(f"⏳ Пауза перед повтором: {jittered_delay:.1f} сек")
                time.sleep(jittered_delay)
        
        return False
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("🔒 Супер-стелс браузер закрыт")
            except Exception as e:
                self.logger.error(f"Ошибка закрытия браузера: {e}")

# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    bot = SuperHumanBrowserBot(headless=True, ultra_stealth=True)
    
    try:
        # Тестируем скачивание проблемного файла
        test_url = "https://court.aifc.kz/files/legals/533/file/comreg_v8_01.01.2023.pdf"
        save_path = "test_download.pdf"
        
        success = bot.smart_download_file(test_url, save_path)
        
        if success:
            print("✅ Тестовое скачивание успешно!")
        else:
            print("❌ Тестовое скачивание не удалось")
    
    finally:
        bot.close()
