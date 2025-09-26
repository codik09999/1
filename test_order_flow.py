import requests
import json
import time

# Конфигурация
BOT_TOKEN = "7808830885:AAHFkGTaOylnQ99RrNolU5UgjEgo2gxFrqo"
ADMIN_CHAT_ID = "2063086506"
WEB_SERVER_URL = "http://127.0.0.1:5000"

def send_telegram_message(text):
    """Отправить сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': ADMIN_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200 and response.json().get('ok', False)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

def get_pending_orders():
    """Получить ожидающие заказы"""
    try:
        response = requests.get(f"{WEB_SERVER_URL}/api/bot/orders", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"Ошибка получения заказов: {e}")
        return {}

def create_test_order():
    """Создать тестовый заказ"""
    try:
        order_data = {
            'name': 'Тест Заказ',
            'phone': '+7999123456',
            'email': 'test@example.com',
            'service': 'premium',
            'message': 'Тестовый заказ для проверки системы'
        }
        
        response = requests.post(
            f"{WEB_SERVER_URL}/api/submit_order",
            json=order_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('order_id')
        return None
    except Exception as e:
        print(f"Ошибка создания заказа: {e}")
        return None

def main():
    print("🧪 ТЕСТИРОВАНИЕ ПОЛНОГО ЦИКЛА ЗАКАЗОВ")
    print("=" * 50)
    
    # 1. Проверяем подключение к серверу
    print("1️⃣ Проверяем веб-сервер...")
    try:
        response = requests.get(WEB_SERVER_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Веб-сервер работает")
        else:
            print("❌ Веб-сервер недоступен")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к серверу: {e}")
        return
    
    # 2. Создаем тестовый заказ
    print("\n2️⃣ Создаем тестовый заказ...")
    order_id = create_test_order()
    
    if order_id:
        print(f"✅ Заказ создан: {order_id[:8]}...")
    else:
        print("❌ Не удалось создать заказ")
        return
    
    # 3. Получаем данные заказа
    print("\n3️⃣ Получаем данные заказа...")
    orders = get_pending_orders()
    
    if order_id in orders:
        order_data = orders[order_id]
        print("✅ Заказ найден в системе")
        
        # 4. Отправляем уведомление в Telegram
        print("\n4️⃣ Отправляем уведомление в Telegram...")
        
        data = order_data['data']
        created_time = order_data['created_at']
        
        message = f"""
🔔 <b>НОВЫЙ ЗАКАЗ!</b>

👤 <b>Имя:</b> {data['name']}
📞 <b>Телефон:</b> {data['phone']}
📧 <b>Email:</b> {data['email']}
🛍 <b>Услуга:</b> {data['service']}
📝 <b>Сообщение:</b> {data.get('message', 'Не указано')}

📅 <b>Время:</b> {created_time}
🆔 <b>ID:</b> {order_id[:8]}...

🔗 <b>Управление:</b> {WEB_SERVER_URL}/api/bot/approve/{order_id}
        """
        
        if send_telegram_message(message):
            print("✅ Уведомление отправлено в Telegram!")
            print("📱 Проверьте своего бота - должно прийти сообщение")
        else:
            print("❌ Не удалось отправить уведомление")
            
    else:
        print("❌ Заказ не найден в системе")
    
    print(f"\n🎯 РЕЗУЛЬТАТ:")
    print(f"📊 Всего заказов в очереди: {len(orders)}")
    print(f"🤖 Ваш бот: @vpn123123_bot")
    print(f"🌐 Сайт: {WEB_SERVER_URL}")

if __name__ == "__main__":
    main()