@echo off
chcp 65001 >nul
title AIFC Court Document Monitor

echo ==========================================
echo    AIFC Court Document Monitor
echo ==========================================
echo.
echo Выберите режим работы:
echo 1. Однократная проверка
echo 2. Непрерывный мониторинг
echo 3. Установить зависимости
echo 4. Выход
echo.

set /p choice="Введите номер (1-4): "

if "%choice%"=="1" goto once
if "%choice%"=="2" goto continuous
if "%choice%"=="3" goto install
if "%choice%"=="4" goto exit
goto invalid

:once
echo.
echo Запуск однократной проверки...
python run_aifc_monitor.py --once
pause
goto menu

:continuous
echo.
echo Запуск непрерывного мониторинга...
echo Для остановки нажмите Ctrl+C
python run_aifc_monitor.py
pause
goto menu

:install
echo.
echo Установка зависимостей...
pip install -r requirements.txt
echo.
echo Зависимости установлены!
pause
goto menu

:invalid
echo.
echo Неверный выбор! Попробуйте снова.
pause

:menu
cls
goto start

:exit
echo.
echo До свидания!
timeout /t 2 >nul