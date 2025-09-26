@echo off
echo ===========================================
echo     ЗАПУСК СИСТЕМЫ ЗАКАЗОВ
echo ===========================================
echo.
echo 🚀 Запускаем веб-сервер...
start "WEB-СЕРВЕР" cmd /k "python app.py"
echo.
echo ⏳ Ждем 3 секунды...
timeout /t 3 /nobreak >nul
echo.
echo 🤖 Запускаем Telegram бота...
start "TELEGRAM-БОТ" cmd /k "python simple_bot.py"
echo.
echo ✅ Оба компонента запущены!
echo.
echo 📝 Что дальше:
echo 1. Откройте http://127.0.0.1:5000
echo 2. Нажмите "Сделать заказ"
echo 3. Заполните форму
echo 4. Проверьте Telegram
echo.
echo 📊 Проверить статус: python check_system.py
echo.
pause