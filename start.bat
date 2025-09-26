@echo off
echo ===============================================
echo         СИСТЕМА ЗАКАЗОВ С TELEGRAM БОТОМ
echo ===============================================
echo.
echo 1. Проверяем зависимости...
pip install -r requirements.txt
echo.
echo 2. Запускаем веб-сервер...
echo.
echo ВНИМАНИЕ: После запуска сервера откройте новое окно командной строки
echo и запустите там: python telegram_bot.py
echo.
echo Сайт будет доступен по адресу: http://127.0.0.1:5000
echo.
echo Для остановки нажмите Ctrl+C
echo.
python app.py