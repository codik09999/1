import logging
import requests
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация через переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')  # Получите от @BotFather
WEB_SERVER_URL = os.environ.get('WEB_SERVER_URL', 'http://127.0.0.1:5000')  # URL вашего веб-сервера
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', 'YOUR_CHAT_ID_HERE')  # Ваш chat_id для получения уведомлений

class OrderBot:
    def __init__(self, token, web_server_url):
        self.token = token
        self.web_server_url = web_server_url
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и callback'ов"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_message = """
🤖 Добро пожаловать в систему управления заказами!

Доступные команды:
/orders - Показать активные заказы
/help - Помощь

Этот бот будет уведомлять вас о новых заказах с сайта.
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
📝 Помощь по использованию бота:

🔸 /start - Приветствие и информация
🔸 /orders - Показать все ожидающие заказы
🔸 /help - Показать это сообщение

🔄 Автоматические уведомления:
- Когда пользователь оформляет заказ на сайте, вы получите уведомление
- Нажмите ✅ "Подтвердить" чтобы одобрить заказ
- Нажмите ❌ "Отклонить" чтобы отклонить заказ
- После подтверждения пользователь получит код для ввода
        """
        await update.message.reply_text(help_text)
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /orders - показать все ожидающие заказы"""
        try:
            response = requests.get(f"{self.web_server_url}/api/bot/orders")
            if response.status_code == 200:
                orders = response.json()
                
                if not orders:
                    await update.message.reply_text("📋 Нет ожидающих заказов")
                    return
                
                for order_id, order_data in orders.items():
                    await self.send_order_notification(update.effective_chat.id, order_id, order_data)
            else:
                await update.message.reply_text("❌ Ошибка получения заказов с сервера")
                
        except Exception as e:
            logger.error(f"Ошибка получения заказов: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении заказов")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        action, order_id = query.data.split("_", 1)
        
        if action == "approve":
            await self.approve_order(query, order_id)
        elif action == "reject":
            await self.reject_order(query, order_id)
        elif action == "details":
            await self.show_order_details(query, order_id)
    
    async def approve_order(self, query, order_id):
        """Подтвердить заказ"""
        try:
            response = requests.post(f"{self.web_server_url}/api/bot/approve/{order_id}")
            
            if response.status_code == 200:
                data = response.json()
                confirmation_code = data.get('confirmation_code')
                
                success_message = f"""
✅ Заказ подтвержден!

🔑 Код подтверждения: `{confirmation_code}`

Пользователь получил уведомление о подтверждении заказа.
Теперь он должен ввести код подтверждения на сайте.
                """
                
                # Обновляем сообщение
                await query.edit_message_text(
                    text=success_message,
                    parse_mode='Markdown'
                )
                
                logger.info(f"Заказ {order_id} подтвержден администратором")
            else:
                await query.edit_message_text("❌ Ошибка подтверждения заказа")
                
        except Exception as e:
            logger.error(f"Ошибка подтверждения заказа: {e}")
            await query.edit_message_text("❌ Произошла ошибка при подтверждении заказа")
    
    async def reject_order(self, query, order_id):
        """Отклонить заказ"""
        try:
            response = requests.post(f"{self.web_server_url}/api/bot/reject/{order_id}")
            
            if response.status_code == 200:
                await query.edit_message_text("❌ Заказ отклонен. Пользователь получил уведомление.")
                logger.info(f"Заказ {order_id} отклонен администратором")
            else:
                await query.edit_message_text("❌ Ошибка отклонения заказа")
                
        except Exception as e:
            logger.error(f"Ошибка отклонения заказа: {e}")
            await query.edit_message_text("❌ Произошла ошибка при отклонении заказа")
    
    async def show_order_details(self, query, order_id):
        """Показать детали заказа"""
        try:
            response = requests.get(f"{self.web_server_url}/api/bot/order/{order_id}")
            
            if response.status_code == 200:
                order = response.json()
                order_data = order['data']
                
                details_message = f"""
📋 Детали заказа:

👤 Имя: {order_data['name']}
📞 Телефон: {order_data['phone']}
📧 Email: {order_data['email']}
🛍 Услуга: {order_data['service']}
📝 Сообщение: {order_data.get('message', 'Не указано')}

📅 Создан: {order['created_at']}
🔄 Статус: {order['status']}
                """
                
                # Создаем кнопки действий
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{order_id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=details_message,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text("❌ Заказ не найден")
                
        except Exception as e:
            logger.error(f"Ошибка получения деталей заказа: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении деталей заказа")
    
    async def send_order_notification(self, chat_id, order_id, order_data):
        """Отправить уведомление о новом заказе"""
        try:
            data = order_data['data']
            created_time = datetime.fromisoformat(order_data['created_at']).strftime('%d.%m.%Y %H:%M')
            
            message = f"""
🔔 НОВЫЙ ЗАКАЗ!

👤 Имя: {data['name']}
📞 Телефон: {data['phone']}
📧 Email: {data['email']}
🛍 Услуга: {data['service']}
📝 Сообщение: {data.get('message', 'Не указано')}

📅 Время: {created_time}
🆔 ID: {order_id[:8]}...

Выберите действие:
            """
            
            # Создаем inline клавиатуру с кнопками
            keyboard = [
                [
                    InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{order_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
                ],
                [
                    InlineKeyboardButton("📋 Детали", callback_data=f"details_{order_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    async def notify_new_order(self, order_id, order_data):
        """Уведомить администратора о новом заказе"""
        if ADMIN_CHAT_ID and ADMIN_CHAT_ID != "YOUR_CHAT_ID_HERE":
            await self.send_order_notification(ADMIN_CHAT_ID, order_id, order_data)
    
    async def run_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск Telegram бота...")
        await self.application.run_polling()
    
    def run(self):
        """Запуск бота"""
        logger.info("Инициализация Telegram бота...")
        
        if self.token == "YOUR_BOT_TOKEN_HERE":
            logger.error("❌ Не установлен BOT_TOKEN! Получите токен у @BotFather")
            return
        
        if ADMIN_CHAT_ID == "YOUR_CHAT_ID_HERE":
            logger.warning("⚠️ Не установлен ADMIN_CHAT_ID. Автоматические уведомления отключены.")
        
        # Запуск polling
        self.application.run_polling()

# Класс для мониторинга новых заказов
class OrderMonitor:
    def __init__(self, bot, web_server_url):
        self.bot = bot
        self.web_server_url = web_server_url
        self.last_check_orders = set()
    
    async def monitor_orders(self):
        """Мониторинг новых заказов"""
        while True:
            try:
                response = requests.get(f"{self.web_server_url}/api/bot/orders", timeout=5)
                if response.status_code == 200:
                    current_orders = response.json()
                    current_order_ids = set(current_orders.keys())
                    
                    # Находим новые заказы
                    new_orders = current_order_ids - self.last_check_orders
                    
                    for order_id in new_orders:
                        order_data = current_orders[order_id]
                        await self.bot.notify_new_order(order_id, order_data)
                        logger.info(f"Отправлено уведомление о заказе {order_id}")
                    
                    self.last_check_orders = current_order_ids
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга заказов: {e}")
            
            await asyncio.sleep(3)  # Проверка каждые 3 секунды

def main():
    """Основная функция"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ОШИБКА: Не установлен BOT_TOKEN!")
        print("1. Создайте бота через @BotFather")
        print("2. Получите токен")
        print("3. Замените 'YOUR_BOT_TOKEN_HERE' в файле telegram_bot.py")
        return
    
    if ADMIN_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("⚠️ ВНИМАНИЕ: Не установлен ADMIN_CHAT_ID!")
        print("1. Найдите своего chat_id через @userinfobot")
        print("2. Замените 'YOUR_CHAT_ID_HERE' в файле telegram_bot.py")
        print("3. Автоматические уведомления о заказах будут отключены")
        print()
    
    # Создание и запуск бота
    bot = OrderBot(BOT_TOKEN, WEB_SERVER_URL)
    
    print("🤖 Telegram бот запущен!")
    print(f"📡 Подключение к серверу: {WEB_SERVER_URL}")
    print("📱 Доступные команды:")
    print("   /start - Приветствие")
    print("   /orders - Показать активные заказы")
    print("   /help - Помощь")
    print()
    print("🔄 Для остановки нажмите Ctrl+C")
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()