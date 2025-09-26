import requests
import json

# Конфигурация
BOT_TOKEN = "7808830885:AAHFkGTaOylnQ99RrNolU5UgjEgo2gxFrqo"
ADMIN_CHAT_ID = "2063086506"

def test_bot_token():
    """Проверить валидность токена бота"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот найден: @{bot_info['username']} ({bot_info['first_name']})")
                return True
            else:
                print(f"❌ Ошибка API: {data}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def test_send_message():
    """Попробовать отправить тестовое сообщение"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': ADMIN_CHAT_ID,
            'text': '🧪 Тестовое сообщение от системы заказов!\n\nЕсли вы видите это сообщение, то бот работает правильно.',
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Тестовое сообщение отправлено успешно!")
                return True
            else:
                print(f"❌ Ошибка отправки: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка при отправке: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False

def test_chat_id():
    """Проверить chat_id"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        data = {'chat_id': ADMIN_CHAT_ID}
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                chat_info = result['result']
                print(f"✅ Chat ID корректный: {chat_info.get('first_name', 'N/A')} {chat_info.get('last_name', '')}")
                return True
            else:
                print(f"❌ Неверный Chat ID: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка при проверке chat: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки chat_id: {e}")
        return False

def main():
    print("🔍 ТЕСТИРОВАНИЕ TELEGRAM БОТА")
    print("=" * 50)
    print(f"🤖 Токен бота: {BOT_TOKEN[:20]}...")
    print(f"👤 Chat ID: {ADMIN_CHAT_ID}")
    print()
    
    print("1️⃣ Проверяем токен бота...")
    token_ok = test_bot_token()
    print()
    
    print("2️⃣ Проверяем chat_id...")
    chat_ok = test_chat_id()
    print()
    
    if token_ok and chat_ok:
        print("3️⃣ Отправляем тестовое сообщение...")
        message_ok = test_send_message()
        print()
        
        if message_ok:
            print("🎉 ВСЁ РАБОТАЕТ!")
            print("✅ Проверьте Telegram - должно прийти тестовое сообщение")
        else:
            print("❌ Проблема с отправкой сообщений")
    else:
        print("❌ Основные настройки неверны")
        if not token_ok:
            print("   → Проверьте токен бота")
        if not chat_ok:
            print("   → Проверьте chat_id")
    
    print("\n📝 ИНСТРУКЦИИ:")
    print("1. Найдите вашего бота в Telegram")
    print("2. Напишите ему /start")
    print("3. Попробуйте снова")

if __name__ == "__main__":
    main()