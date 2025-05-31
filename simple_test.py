#!/usr/bin/env python3
"""
Простой тест скачивания документов с AIFC Court
"""

import os
import logging
from browser_bot import AdvancedBrowserBot

def simple_aifc_test():
    """Простой тест скачивания"""
    print("🤖 === Простой тест AIFC Court ===")
    print("=" * 40)
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем папку для документов
    download_dir = "aifc_documents"
    os.makedirs(download_dir, exist_ok=True)
    
    try:
        # Инициализируем браузерный бот
        print("🚀 Инициализация браузерного бота...")
        bot = AdvancedBrowserBot(headless=True, stealth_mode=True)
        
        # Переходим на страницу с решениями
        print("🌐 Открываем страницу с решениями суда...")
        success = bot.visit_page_like_human("https://court.aifc.kz/en/judgments")
        
        if success:
            print("✅ Страница загружена успешно")
            
            # Ищем документы
            print("🔍 Ищем документы...")
            documents = bot.find_document_links()
            
            print(f"📊 Найдено документов: {len(documents)}")
            
            if documents:
                # Скачиваем первый документ
                first_doc = documents[0]
                print(f"📥 Скачиваем: {first_doc['url']}")
                
                # Получаем имя файла
                filename = os.path.basename(first_doc['url']).replace('%20', '_')
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
                
                save_path = os.path.join(download_dir, filename)
                
                # Скачиваем через браузер
                bot.visit_page_like_human(first_doc['url'])
                
                # Используем requests для скачивания с куками браузера
                import requests
                
                cookies = bot.driver.get_cookies()
                session_cookies = {}
                for cookie in cookies:
                    session_cookies[cookie['name']] = cookie['value']
                
                headers = {
                    'User-Agent': bot.driver.execute_script("return navigator.userAgent;"),
                    'Referer': 'https://court.aifc.kz/en/judgments'
                }
                
                response = requests.get(first_doc['url'], headers=headers, cookies=session_cookies, stream=True)
                response.raise_for_status()
                
                # Сохраняем файл
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Файл сохранен: {save_path}")
                print(f"📊 Размер файла: {len(response.content)} байт")
                
                # Проверяем что файл создался
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    print("🎉 УСПЕХ! Документ успешно скачан!")
                else:
                    print("❌ Ошибка: файл не создался или пустой")
                    
            else:
                print("❌ Документы не найдены")
        else:
            print("❌ Не удалось загрузить страницу")
        
        # Закрываем браузер
        print("🔒 Закрываем браузер...")
        bot.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 40)
    print("🏁 Тест завершен")

if __name__ == "__main__":
    simple_aifc_test()