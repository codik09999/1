#!/usr/bin/env python3
"""
Скрипт для запуска веб-приложения и Telegram бота в продакшн режиме
Используется для развертывания на Railway
"""

import os
import threading
import time
import logging
from multiprocessing import Process

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_web_app():
    """Запуск веб-приложения Flask"""
    logger.info("Запуск Flask веб-приложения...")
    try:
        # Импортируем и запускаем Flask app
        from app import app, socketio
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        socketio.run(app, host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Ошибка запуска веб-приложения: {e}")

def start_telegram_bot():
    """Запуск Telegram бота"""
    logger.info("Запуск Telegram бота...")
    try:
        # Небольшая задержка для запуска веб-сервера
        time.sleep(5)
        
        # Импортируем и запускаем бота
        from telegram_bot import OrderBot, WEB_SERVER_URL, BOT_TOKEN
        
        if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.warning("⚠️ BOT_TOKEN не установлен. Telegram бот не запущен.")
            return
            
        bot = OrderBot(BOT_TOKEN, WEB_SERVER_URL)
        bot.run()
    except Exception as e:
        logger.error(f"Ошибка запуска Telegram бота: {e}")

def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск производственной версии VPN сервиса")
    
    # Проверяем переменные окружения
    required_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.warning(f"⚠️ Не установлены переменные окружения: {', '.join(missing_vars)}")
    
    # На Railway обычно запускается только веб-приложение
    # Telegram бот можно запустить отдельно или в фоне
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info("🚄 Обнаружена среда Railway - запуск только веб-приложения")
        start_web_app()
    else:
        logger.info("🖥️ Локальная среда - запуск обоих сервисов")
        # В локальной среде запускаем оба сервиса
        web_process = Process(target=start_web_app)
        bot_process = Process(target=start_telegram_bot)
        
        web_process.start()
        bot_process.start()
        
        try:
            web_process.join()
            bot_process.join()
        except KeyboardInterrupt:
            logger.info("👋 Остановка сервисов...")
            web_process.terminate()
            bot_process.terminate()

if __name__ == "__main__":
    main()