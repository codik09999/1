import requests
import json

def check_web_server():
    """Проверить состояние веб-сервера"""
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Веб-сервер работает: http://127.0.0.1:5000")
            return True
        else:
            print(f"❌ Веб-сервер недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Веб-сервер не отвечает: {e}")
        return False

def check_bot_api():
    """Проверить API для бота"""
    try:
        response = requests.get("http://127.0.0.1:5000/api/bot/orders", timeout=5)
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ API бота работает. Заказов в очереди: {len(orders)}")
            if orders:
                print("📋 Активные заказы:")
                for order_id, order_data in orders.items():
                    data = order_data['data']
                    print(f"  - {data['name']} ({data['phone']}) - {data['service']}")
            return True
        else:
            print(f"❌ API бота недоступно: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API бота не отвечает: {e}")
        return False

def main():
    print("🔍 ПРОВЕРКА СИСТЕМЫ ЗАКАЗОВ")
    print("=" * 40)
    
    web_ok = check_web_server()
    api_ok = check_bot_api()
    
    print("\n📊 СТАТУС СИСТЕМЫ")
    print("=" * 40)
    
    if web_ok and api_ok:
        print("🎉 Система полностью работает!")
        print("🌐 Сайт: http://127.0.0.1:5000")
        print("🤖 Убедитесь что Telegram бот запущен")
        print("\n📝 ТЕСТ:")
        print("1. Откройте сайт")
        print("2. Нажмите 'Сделать заказ'")
        print("3. Заполните форму")
        print("4. Проверьте Telegram")
    else:
        print("❌ Система работает не полностью")
        if not web_ok:
            print("   → Запустите: python app.py")
        if not api_ok:
            print("   → Проверьте веб-сервер")

if __name__ == "__main__":
    main()