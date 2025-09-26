import logging
import requests
import json
import time
import threading
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "7808830885:AAHFkGTaOylnQ99RrNolU5UgjEgo2gxFrqo"
WEB_SERVER_URL = "http://127.0.0.1:5000"
ADMIN_CHAT_ID = "2063086506"

class SimpleOrderBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.last_orders = set()
        self.monitoring = True
        self.setup_handlers()
        logger.info("Бот инициализирован")
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        message = """
🤖 <b>Система заказов готова!</b>

✅ Бот активен и отслеживает новые заказы
✅ Автоматические уведомления включены
✅ Сайт работает: http://127.0.0.1:5000

<b>Команды:</b>
/orders - Показать все заказы
/help - Помощь

Как только поступит новый заказ, вы получите уведомление с кнопками для подтверждения или отклонения.
        """
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        message = """
📖 <b>Помощь по системе заказов</b>

<b>Автоматический режим:</b>
• При новом заказе вы получите уведомление
• Нажмите ✅ "Подтвердить" для одобрения
• Нажмите ❌ "Отклонить" для отказа
• После подтверждения пользователь получит код

<b>Команды:</b>
/start - Информация о боте
/orders - Показать активные заказы
/help - Эта справка

🌐 Сайт: http://127.0.0.1:5000
        """
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать все заказы"""
        try:
            response = requests.get(f"{WEB_SERVER_URL}/api/bot/orders", timeout=5)
            if response.status_code == 200:
                orders = response.json()
                
                if not orders:
                    await update.message.reply_text("📋 Нет ожидающих заказов")
                    return
                
                for order_id, order_data in orders.items():
                    await self.send_order_notification(update.effective_chat.id, order_id, order_data)
            else:
                await update.message.reply_text("❌ Ошибка получения заказов")
        except Exception as e:
            logger.error(f"Ошибка получения заказов: {e}")
            await update.message.reply_text("❌ Не удалось получить заказы")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопок"""
        query = update.callback_query
        await query.answer()
        
        try:
            action, order_id = query.data.split("_", 1)
            
            if action == "approve":
                await self.approve_order(query, order_id)
            elif action == "reject":
                await self.reject_order(query, order_id)
            elif action == "confirm":
                await self.confirm_code(query, order_id)
        except Exception as e:
            logger.error(f"Ошибка обработки кнопки: {e}")
            await query.edit_message_text("❌ Ошибка обработки действия")
    
    async def approve_order(self, query, order_id):
        """Подтвердить заказ"""
        try:
            response = requests.post(f"{WEB_SERVER_URL}/api/bot/approve/{order_id}", timeout=5)
            
            if response.status_code == 200:
                message = f"""
✅ <b>ЗАКАЗ ОДОБРЕН!</b>

Пользователь может ввести свой код на сайте.
Ожидайте уведомление с кодом пользователя.

🌐 Сайт: {WEB_SERVER_URL}
                """
                
                await query.edit_message_text(message, parse_mode='HTML')
                logger.info(f"Заказ {order_id} одобрен")
            else:
                await query.edit_message_text("❌ Ошибка одобрения заказа")
        except Exception as e:
            logger.error(f"Ошибка одобрения: {e}")
            await query.edit_message_text("❌ Не удалось одобрить заказ")
    
    async def reject_order(self, query, order_id):
        """Отклонить заказ"""
        try:
            response = requests.post(f"{WEB_SERVER_URL}/api/bot/reject/{order_id}", timeout=5)
            
            if response.status_code == 200:
                await query.edit_message_text("❌ Заказ отклонен. Пользователь уведомлен.")
                logger.info(f"Заказ {order_id} отклонен")
            else:
                await query.edit_message_text("❌ Ошибка отклонения заказа")
        except Exception as e:
            logger.error(f"Ошибка отклонения: {e}")
            await query.edit_message_text("❌ Не удалось отклонить заказ")
    
    async def confirm_code(self, query, order_id):
        """Подтвердить код пользователя"""
        try:
            response = requests.post(f"{WEB_SERVER_URL}/api/bot/confirm_code/{order_id}", timeout=5)
            
            if response.status_code == 200:
                message = "✅ Код подтвержден! Заказ успешно завершен."
                await query.edit_message_text(message)
                logger.info(f"Код для заказа {order_id} подтвержден")
            else:
                await query.edit_message_text("❌ Ошибка подтверждения кода")
        except Exception as e:
            logger.error(f"Ошибка подтверждения кода: {e}")
            await query.edit_message_text("❌ Не удалось подтвердить код")
    
    async def send_order_notification(self, chat_id, order_id, order_data):
        """Отправить уведомление о заказе"""
        try:
            data = order_data['data']
            status = order_data.get('status', 'pending')
            created_time = datetime.fromisoformat(order_data['created_at']).strftime('%d.%m.%Y %H:%M')
            
            if status == 'code_submitted':
                user_code = order_data.get('user_code', '?')
                message = f"""
🔑 <b>КОД ОТ ПОЛЬЗОВАТЕЛЯ!</b>

👤 <b>Имя:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📧 <b>Email:</b> {data['email']}

🔑 <b>Код пользователя:</b> <code>{user_code}</code>

🆔 <b>ID заказа:</b> {order_id[:8]}...

<b>Подтвердить код?</b>
                """
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Подтвердить код", callback_data=f"confirm_{order_id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
                    ]
                ]
            else:
                message = f"""
🔔 <b>НОВЫЙ ЗАКАЗ!</b>

👤 <b>Имя:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📧 <b>Email:</b> {data['email']}
🛍 <b>Услуга:</b> {data['service']}
📝 <b>Сообщение:</b> {data.get('message', 'Не указано')}

📅 <b>Время:</b> {created_time}
🆔 <b>ID:</b> {order_id[:8]}...

<b>Выберите действие:</b>
                """
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{order_id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{order_id}")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def monitor_orders(self):
        """Мониторинг заказов в отдельном потоке"""
        logger.info("Запуск мониторинга заказов")
        
        while self.monitoring:
            try:
                response = requests.get(f"{WEB_SERVER_URL}/api/bot/orders", timeout=5)
                if response.status_code == 200:
                    current_orders = response.json()
                    current_order_ids = set(current_orders.keys())
                    
                    # Находим новые заказы
                    new_orders = current_order_ids - self.last_orders
                    
                    if new_orders and ADMIN_CHAT_ID:
                        for order_id in new_orders:
                            try:
                                order_data = current_orders[order_id]
                                # Отправляем напрямую через requests API
                                self.send_telegram_notification(order_id, order_data)
                                logger.info(f"Отправлено уведомление о заказе {order_id}")
                            except Exception as e:
                                logger.error(f"Ошибка отправки уведомления для {order_id}: {e}")
                    
                    self.last_orders = current_order_ids
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
            
            time.sleep(2)  # Проверка каждые 2 секунды
    
    def send_telegram_notification(self, order_id, order_data):
        """Отправка уведомления через API"""
        try:
            data = order_data['data']
            status = order_data.get('status', 'pending')
            created_time = datetime.fromisoformat(order_data['created_at']).strftime('%d.%m.%Y %H:%M')
            
            if status == 'code_submitted':
                user_code = order_data.get('user_code', '?')
                message = f"""🔑 <b>КОД ОТ ПОЛЬЗОВАТЕЛЯ!</b>

👤 <b>Имя:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📧 <b>Email:</b> {data['email']}

🔑 <b>Код пользователя:</b> <code>{user_code}</code>

🆔 <b>ID заказа:</b> {order_id[:8]}...

<b>Подтвердить код?</b>"""
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Подтвердить код", "callback_data": f"confirm_{order_id}"},
                            {"text": "❌ Отклонить", "callback_data": f"reject_{order_id}"}
                        ]
                    ]
                }
            else:
                message = f"""🔔 <b>НОВЫЙ ЗАКАЗ!</b>

👤 <b>Имя:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📧 <b>Email:</b> {data['email']}
🛍 <b>Услуга:</b> {data['service']}
📝 <b>Сообщение:</b> {data.get('message', 'Не указано')}

📅 <b>Время:</b> {created_time}
🆔 <b>ID:</b> {order_id[:8]}...

<b>Выберите действие:</b>"""
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Одобрить", "callback_data": f"approve_{order_id}"},
                            {"text": "❌ Отклонить", "callback_data": f"reject_{order_id}"}
                        ]
                    ]
                }
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Ошибка отправки через API: {e}")
            return False
    
    def run(self):
        """Запуск бота"""
        print("🤖 Запуск упрощенного бота...")
        print(f"📡 Сервер: {WEB_SERVER_URL}")
        print(f"👤 Admin ID: {ADMIN_CHAT_ID}")
        print("🔄 Мониторинг каждые 2 секунды")
        print("⚠️ Для остановки: Ctrl+C")
        print()
        
        # Запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=self.monitor_orders, daemon=True)
        monitor_thread.start()
        
        try:
            self.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            print("\n👋 Остановка бота...")
            self.monitoring = False

def main():
    bot = SimpleOrderBot()
    bot.run()

if __name__ == "__main__":
    main()