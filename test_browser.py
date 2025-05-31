#!/usr/bin/env python3
"""
Тестирование браузерного бота
"""

import logging
import sys

def test_browser_bot():
    """Тест браузерного бота"""
    print("🧪 Тестирование браузерного бота...")
    
    try:
        from browser_bot import AdvancedBrowserBot
        
        # Инициализация с GUI для просмотра (headless=False)
        print("🚀 Инициализация браузера...")
        bot = AdvancedBrowserBot(headless=False, stealth_mode=True)
        
        # Тест посещения страницы
        print("🌐 Тестируем посещение главной страницы...")
        success = bot.visit_page_like_human("https://court.aifc.kz")
        
        if success:
            print("✅ Главная страница загружена успешно")
            
            # Тест поиска документов на странице judgments
            print("📄 Тестируем поиск документов...")
            success = bot.visit_page_like_human("https://court.aifc.kz/en/judgments")
            
            if success:
                documents = bot.find_document_links()
                print(f"📊 Найдено документов: {len(documents)}")
                
                for i, doc in enumerate(documents[:5]):  # Показываем первые 5
                    print(f"  {i+1}. {doc['url']}")
                    
                if len(documents) > 5:
                    print(f"  ... и еще {len(documents) - 5} документов")
                    
            else:
                print("❌ Не удалось загрузить страницу judgments")
        else:
            print("❌ Не удалось загрузить главную страницу")
        
        # Закрываем браузер
        print("🔒 Закрываем браузер...")
        bot.close()
        
        return len(documents) if 'documents' in locals() else 0
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь что файл browser_bot.py находится в той же папке")
        return -1
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return -1

def test_chrome_availability():
    """Проверка доступности Chrome"""
    print("🔍 Проверяем доступность Chrome...")
    
    try:
        import undetected_chromedriver as uc
        
        # Пробуем создать простой драйвер с минимальными опциями
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        print("🚀 Создаем тестовый драйвер...")
        driver = uc.Chrome(options=options, version_main=None)
        
        print("🌐 Тестируем загрузку страницы...")
        driver.get("https://httpbin.org/user-agent")
        
        # Получаем User-Agent
        body_element = driver.find_element("tag name", "body")
        user_agent_text = body_element.text
        
        print("🔒 Закрываем тестовый драйвер...")
        driver.quit()
        
        print("✅ Chrome доступен и работает")
        print(f"Информация: {user_agent_text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Chrome недоступен: {e}")
        print("Решения:")
        print("1. Установите Google Chrome: https://www.google.com/chrome/")
        print("2. Обновите Chrome до последней версии")
        print("3. Перезапустите компьютер после установки")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 50)
    print("  ТЕСТИРОВАНИЕ БРАУЗЕРНОГО БОТА")
    print("=" * 50)
    
    # Проверяем Chrome
    chrome_ok = test_chrome_availability()
    
    if chrome_ok:
        # Тестируем браузерный бот
        doc_count = test_browser_bot()
        
        print("\n" + "=" * 50)
        if doc_count > 0:
            print(f"🎉 ТЕСТ УСПЕШЕН! Найдено {doc_count} документов")
            print("Браузерный бот готов к работе!")
        elif doc_count == 0:
            print("⚠️ Браузер работает, но документы не найдены")
            print("Возможно, сайт изменил структуру")
        else:
            print("❌ ТЕСТ НЕ ПРОЙДЕН")
            print("Проверьте настройки и попробуйте снова")
    else:
        print("\n❌ Установите Chrome для работы браузерного бота")
    
    print("=" * 50)
