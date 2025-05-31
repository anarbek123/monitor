"""
Генератор отчетов для AIFC Court Document Monitor
"""

import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

class ReportGenerator:
    def __init__(self, download_dir="aifc_documents"):
        self.download_dir = download_dir
        self.logger = logging.getLogger(__name__)
        
    def load_data(self):
        """Загрузка данных из файлов системы"""
        try:
            # Загружаем историю скачанных файлов
            with open('downloaded_files.json', 'r', encoding='utf-8') as f:
                downloaded_files = json.load(f)
        except FileNotFoundError:
            downloaded_files = {}
            
        try:
            # Загружаем обнаруженные файлы
            with open('discovered_files.json', 'r', encoding='utf-8') as f:
                discovered_files = json.load(f)
        except FileNotFoundError:
            discovered_files = {'files': {}}
            
        try:
            # Проверяем статус первого запуска
            with open('first_run_completed.json', 'r', encoding='utf-8') as f:
                first_run_data = json.load(f)
        except FileNotFoundError:
            first_run_data = {'completed': False}
            
        return downloaded_files, discovered_files, first_run_data
    
    def analyze_file_structure(self):
        """Анализ структуры файлов на диске"""
        structure = {}
        total_size = 0
        file_count = 0
        
        if not os.path.exists(self.download_dir):
            return structure, total_size, file_count
            
        for root, dirs, files in os.walk(self.download_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    file_count += 1
                    
                    # Получаем относительный путь от базовой директории
                    rel_path = os.path.relpath(root, self.download_dir)
                    
                    if rel_path not in structure:
                        structure[rel_path] = {
                            'files': [],
                            'total_size': 0,
                            'count': 0
                        }
                    
                    structure[rel_path]['files'].append({
                        'name': file,
                        'size': file_size,
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                    })
                    structure[rel_path]['total_size'] += file_size
                    structure[rel_path]['count'] += 1
                    
                except OSError:
                    continue
                    
        return structure, total_size, file_count
    
    def categorize_documents(self, downloaded_files):
        """Категоризация документов по типам"""
        categories = {
            'judgments': {
                'by_year': defaultdict(list),
                'total': 0,
                'size': 0
            },
            'legislation': {
                'by_type': defaultdict(list),
                'total': 0,
                'size': 0
            },
            'other': {
                'files': [],
                'total': 0,
                'size': 0
            }
        }
        
        for url, info in downloaded_files.items():
            file_size = info.get('size', 0)
            
            if 'judgment' in url.lower() or '/uploads/' in url.lower():
                # Извлекаем год из URL
                year_match = re.search(r'20\d{2}', url)
                year = year_match.group() if year_match else 'Unknown'
                
                categories['judgments']['by_year'][year].append({
                    'url': url,
                    'path': info.get('path', ''),
                    'size': file_size,
                    'downloaded_at': info.get('downloaded_at', '')
                })
                categories['judgments']['total'] += 1
                categories['judgments']['size'] += file_size
                
            elif 'legislation' in url.lower():
                # Определяем тип законодательства
                leg_type = 'General'
                if 'companies' in url.lower():
                    leg_type = 'Companies'
                elif 'partnership' in url.lower():
                    leg_type = 'Partnership'
                elif 'financial' in url.lower():
                    leg_type = 'Financial Services'
                elif 'aml' in url.lower() or 'anti-money' in url.lower():
                    leg_type = 'AML/CFT'
                elif 'fees' in url.lower():
                    leg_type = 'Fees'
                elif 'conduct' in url.lower():
                    leg_type = 'Conduct of Business'
                
                categories['legislation']['by_type'][leg_type].append({
                    'url': url,
                    'path': info.get('path', ''),
                    'size': file_size,
                    'downloaded_at': info.get('downloaded_at', '')
                })
                categories['legislation']['total'] += 1
                categories['legislation']['size'] += file_size
                
            else:
                categories['other']['files'].append({
                    'url': url,
                    'path': info.get('path', ''),
                    'size': file_size,
                    'downloaded_at': info.get('downloaded_at', '')
                })
                categories['other']['total'] += 1
                categories['other']['size'] += file_size
                
        return categories
    
    def format_size(self, size_bytes):
        """Форматирование размера файла"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def analyze_activity(self, downloaded_files):
        """Анализ активности скачивания"""
        activity = {
            'by_date': defaultdict(int),
            'by_hour': defaultdict(int),
            'by_method': defaultdict(int),
            'recent_activity': []
        }
        
        now = datetime.now()
        recent_threshold = now - timedelta(days=7)
        
        for url, info in downloaded_files.items():
            try:
                download_time = datetime.fromisoformat(info.get('downloaded_at', ''))
                
                # По дням
                date_str = download_time.strftime('%Y-%m-%d')
                activity['by_date'][date_str] += 1
                
                # По часам
                hour = download_time.hour
                activity['by_hour'][hour] += 1
                
                # По методам
                method = info.get('method', 'unknown')
                activity['by_method'][method] += 1
                
                # Недавняя активность
                if download_time >= recent_threshold:
                    activity['recent_activity'].append({
                        'url': url,
                        'path': info.get('path', ''),
                        'size': info.get('size', 0),
                        'time': download_time,
                        'method': method
                    })
                    
            except (ValueError, TypeError):
                continue
                
        # Сортируем недавнюю активность по времени
        activity['recent_activity'].sort(key=lambda x: x['time'], reverse=True)
        
        return activity
    
    def generate_console_report(self):
        """Генерация отчета для консоли"""
        print("\n" + "=" * 80)
        print("📊 ОТЧЕТ AIFC COURT DOCUMENT MONITOR")
        print("=" * 80)
        
        # Загружаем данные
        downloaded_files, discovered_files, first_run_data = self.load_data()
        structure, total_disk_size, total_disk_files = self.analyze_file_structure()
        categories = self.categorize_documents(downloaded_files)
        activity = self.analyze_activity(downloaded_files)
        
        # Общая информация
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   📁 Папка документов: {self.download_dir}")
        print(f"   📄 Всего файлов на диске: {total_disk_files}")
        print(f"   💾 Общий размер: {self.format_size(total_disk_size)}")
        print(f"   🔗 Файлов в базе данных: {len(downloaded_files)}")
        print(f"   🕐 Первый запуск завершен: {'✅ Да' if first_run_data.get('completed') else '❌ Нет'}")
        
        if first_run_data.get('completed'):
            completed_at = first_run_data.get('completed_at')
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    print(f"   📅 Дата завершения: {completed_time.strftime('%d.%m.%Y %H:%M')}")
                except:
                    pass
        
        # Структура папок
        print(f"\n📂 СТРУКТУРА ПАПОК:")
        for folder, info in sorted(structure.items()):
            if folder == '.':
                folder_name = f"{self.download_dir} (корень)"
            else:
                folder_name = folder.replace('\\', ' → ')
            
            print(f"   📁 {folder_name}")
            print(f"      📄 Файлов: {info['count']}")
            print(f"      💾 Размер: {self.format_size(info['total_size'])}")
            
            # Показываем несколько последних файлов
            recent_files = sorted(info['files'], key=lambda x: x['modified'], reverse=True)[:3]
            for file_info in recent_files:
                print(f"         • {file_info['name']} ({self.format_size(file_info['size'])})")
            
            if len(info['files']) > 3:
                print(f"         ... и еще {len(info['files']) - 3} файлов")
        
        # Категории документов
        print(f"\n📋 КАТЕГОРИИ ДОКУМЕНТОВ:")
        
        # Решения суда
        judgments = categories['judgments']
        print(f"   ⚖️ РЕШЕНИЯ СУДА: {judgments['total']} файлов ({self.format_size(judgments['size'])})")
        for year, files in sorted(judgments['by_year'].items()):
            year_size = sum(f['size'] for f in files)
            print(f"      📅 {year}: {len(files)} решений ({self.format_size(year_size)})")
        
        # Законодательство
        legislation = categories['legislation']
        print(f"   📜 ЗАКОНОДАТЕЛЬСТВО: {legislation['total']} файлов ({self.format_size(legislation['size'])})")
        for leg_type, files in sorted(legislation['by_type'].items()):
            type_size = sum(f['size'] for f in files)
            print(f"      📑 {leg_type}: {len(files)} документов ({self.format_size(type_size)})")
        
        # Прочие документы
        other = categories['other']
        if other['total'] > 0:
            print(f"   📎 ПРОЧИЕ: {other['total']} файлов ({self.format_size(other['size'])})")
        
        # Активность скачивания
        print(f"\n📈 АКТИВНОСТЬ СКАЧИВАНИЯ:")
        
        # По методам
        print(f"   🔧 По методам:")
        for method, count in activity['by_method'].items():
            method_name = {
                'browser_bot': '🤖 Браузерный бот',
                'requests': '📡 HTTP запросы',
                'unknown': '❓ Неизвестно'
            }.get(method, method)
            print(f"      {method_name}: {count} файлов")
        
        # Недавняя активность
        recent = activity['recent_activity'][:10]  # Последние 10
        if recent:
            print(f"\n   🕐 НЕДАВНЯЯ АКТИВНОСТЬ (последние 7 дней):")
            for item in recent:
                time_str = item['time'].strftime('%d.%m %H:%M')
                filename = os.path.basename(item['path']) if item['path'] else 'unknown'
                size_str = self.format_size(item['size'])
                method_icon = '🤖' if item['method'] == 'browser_bot' else '📡'
                print(f"      {method_icon} {time_str} - {filename} ({size_str})")
        
        # Статистика по часам (топ-5)
        hourly_stats = sorted(activity['by_hour'].items(), key=lambda x: x[1], reverse=True)[:5]
        if hourly_stats:
            print(f"\n   ⏰ САМЫЕ АКТИВНЫЕ ЧАСЫ:")
            for hour, count in hourly_stats:
                print(f"      {hour:02d}:00 - {count} файлов")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        
        total_files = len(downloaded_files)
        if total_files == 0:
            print("   • Запустите первое сканирование для скачивания документов")
        elif not first_run_data.get('completed'):
            print("   • Завершите первоначальное сканирование")
        else:
            print("   • Система работает в режиме мониторинга")
            
            # Проверяем свежесть данных
            try:
                last_scan = discovered_files.get('last_full_scan')
                if last_scan:
                    last_time = datetime.fromisoformat(last_scan)
                    days_ago = (datetime.now() - last_time).days
                    if days_ago > 3:
                        print(f"   • Последнее сканирование было {days_ago} дней назад - рекомендуется проверка")
            except:
                pass
                
            if len(recent) == 0:
                print("   • Нет недавней активности - проверьте расписание мониторинга")
        
        print("=" * 80)
    
    def generate_json_report(self, output_file="aifc_report.json"):
        """Генерация JSON отчета"""
        downloaded_files, discovered_files, first_run_data = self.load_data()
        structure, total_disk_size, total_disk_files = self.analyze_file_structure()
        categories = self.categorize_documents(downloaded_files)
        activity = self.analyze_activity(downloaded_files)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'download_directory': self.download_dir,
                'total_files_on_disk': total_disk_files,
                'total_disk_size': total_disk_size,
                'total_disk_size_formatted': self.format_size(total_disk_size),
                'files_in_database': len(downloaded_files),
                'first_run_completed': first_run_data.get('completed', False),
                'first_run_completed_at': first_run_data.get('completed_at')
            },
            'folder_structure': structure,
            'document_categories': categories,
            'activity_analysis': activity,
            'discovered_files_count': len(discovered_files.get('files', {})),
            'last_scan': discovered_files.get('last_full_scan')
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return output_file

def main():
    """Основная функция для запуска отчета"""
    generator = ReportGenerator()
    
    # Генерируем консольный отчет
    generator.generate_console_report()
    
    # Генерируем JSON отчет
    json_file = generator.generate_json_report()
    print(f"\n💾 JSON отчет сохранен: {json_file}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()