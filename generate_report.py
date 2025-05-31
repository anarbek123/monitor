#!/usr/bin/env python3
"""
Генератор отчетов AIFC Court Document Monitor
"""

import sys
import argparse
from report_generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description='Генератор отчетов AIFC Court Document Monitor')
    parser.add_argument('--json', action='store_true', help='Генерировать JSON отчет')
    parser.add_argument('--output', '-o', default='aifc_report.json', help='Имя файла для JSON отчета')
    parser.add_argument('--dir', '-d', default='aifc_documents', help='Директория с документами')
    
    args = parser.parse_args()
    
    print("📊 === ГЕНЕРАТОР ОТЧЕТОВ AIFC COURT ===")
    print("=" * 50)
    
    try:
        generator = ReportGenerator(args.dir)
        
        if args.json:
            # Только JSON отчет
            json_file = generator.generate_json_report(args.output)
            print(f"💾 JSON отчет сохранен: {json_file}")
        else:
            # Консольный отчет
            generator.generate_console_report()
            
            # Предлагаем сохранить JSON
            response = input("\n💾 Сохранить детальный JSON отчет? (y/n): ").lower().strip()
            if response in ['y', 'yes', 'да', 'д']:
                json_file = generator.generate_json_report(args.output)
                print(f"💾 JSON отчет сохранен: {json_file}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())