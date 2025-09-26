"""
Конфигурационный файл для системы заказов
"""

# Flask настройки
FLASK_SECRET_KEY = 'your-secret-key-change-this-in-production'
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Telegram бот настройки
BOT_TOKEN = "7808830885:AAHFkGTaOylnQ99RrNolU5UgjEgo2gxFrqo"  # Получите от @BotFather
ADMIN_CHAT_ID = "2063086506"  # Ваш chat_id для получения уведомлений

# Веб-сервер URL (для бота)
WEB_SERVER_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"

# Настройки заказов
ORDER_TIMEOUT = 1800  # 30 минут на подтверждение заказа
CODE_LENGTH = 6  # Длина кода подтверждения
CODE_EXPIRY = 600  # 10 минут на ввод кода

# WebSocket настройки
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
SOCKETIO_ASYNC_MODE = "threading"

# Логирование
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'