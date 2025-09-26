class OrderManager {
    constructor() {
        this.socket = null;
        this.currentOrderId = null;
        this.init();
    }

    init() {
        this.initializeElements();
        this.bindEvents();
        this.connectWebSocket();
    }

    initializeElements() {
        // Кнопки
        this.orderBtn = document.getElementById('order-btn');
        this.newOrderBtn = document.getElementById('new-order-btn');
        
        // Модальные окна
        this.orderModal = document.getElementById('order-modal');
        this.loadingModal = document.getElementById('loading-modal');
        this.codeModal = document.getElementById('code-modal');
        this.successModal = document.getElementById('success-modal');
        
        // Формы
        this.orderForm = document.getElementById('order-form');
        this.codeForm = document.getElementById('code-form');
        
        // Кнопки закрытия
        this.closeBtns = document.querySelectorAll('.close');
    }

    bindEvents() {
        // Основная кнопка заказа
        this.orderBtn.addEventListener('click', () => {
            this.showModal(this.orderModal);
        });

        // Кнопка нового заказа
        this.newOrderBtn.addEventListener('click', () => {
            this.resetAll();
        });

        // Отправка формы заказа
        this.orderForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitOrder();
        });

        // Отправка кода подтверждения
        this.codeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitConfirmationCode();
        });

        // Закрытие модальных окон
        this.closeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal && modal !== this.loadingModal) {
                    this.hideModal(modal);
                }
            });
        });

        // Закрытие по клику на фон
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal') && 
                e.target !== this.loadingModal) {
                this.hideModal(e.target);
            }
        });

        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal[style*="block"]');
                if (openModal && openModal !== this.loadingModal) {
                    this.hideModal(openModal);
                }
            }
        });
    }

    connectWebSocket() {
        // Используем SocketIO вместо обычных WebSockets
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('SocketIO подключен');
            });
            
            this.socket.on('order_update', (data) => {
                this.handleWebSocketMessage({ data: JSON.stringify(data) });
            });
            
            this.socket.on('disconnect', () => {
                console.log('SocketIO отключен');
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Ошибка SocketIO:', error);
            });
        } catch (error) {
            console.error('Не удалось подключиться к SocketIO:', error);
        }
    }

    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'order_approved':
                    if (data.order_id === this.currentOrderId) {
                        this.hideModal(this.loadingModal);
                        this.showCodeInput();
                    }
                    break;
                    
                case 'order_rejected':
                    if (data.order_id === this.currentOrderId) {
                        this.hideModal(this.loadingModal);
                        this.showError('Заказ отклонен администратором. Попробуйте еще раз.');
                        this.resetAll();
                    }
                    break;
                    
                case 'code_submitted':
                    // Код отправлен администратору, показываем загрузку
                    if (data.order_id === this.currentOrderId) {
                        this.hideModal(this.codeModal);
                        this.showWaitingForConfirmation(data.code);
                    }
                    break;
                    
                case 'code_verified':
                    if (data.order_id === this.currentOrderId) {
                        this.hideModal(this.loadingModal);
                        this.showSuccess();
                    }
                    break;
                    
                case 'code_invalid':
                    if (data.order_id === this.currentOrderId) {
                        this.showError('Ошибка обработки кода. Попробуйте еще раз.');
                        document.getElementById('confirmation-code').focus();
                    }
                    break;
            }
        } catch (error) {
            console.error('Ошибка обработки сообщения WebSocket:', error);
        }
    }

    async submitOrder() {
        const formData = new FormData(this.orderForm);
        const orderData = {
            name: formData.get('name'),
            phone: formData.get('phone'),
            email: formData.get('email'),
            service: formData.get('service'),
            message: formData.get('message')
        };

        // Валидация
        if (!this.validateOrderForm(orderData)) {
            return;
        }

        try {
            const response = await fetch('/api/submit_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            });

            if (response.ok) {
                const result = await response.json();
                this.currentOrderId = result.order_id;
                
                // Скрываем форму заказа и показываем загрузку
                this.hideModal(this.orderModal);
                this.showModal(this.loadingModal);
            } else {
                throw new Error('Ошибка отправки заказа');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            this.showError('Произошла ошибка при отправке заказа. Попробуйте еще раз.');
        }
    }

    async submitConfirmationCode() {
        const code = document.getElementById('confirmation-code').value;
        
        if (!code || code.length < 4) {
            this.showError('Введите корректный код подтверждения');
            return;
        }

        try {
            const response = await fetch('/api/verify_code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order_id: this.currentOrderId,
                    code: code
                })
            });

            if (!response.ok) {
                throw new Error('Ошибка проверки кода');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            this.showError('Произошла ошибка при проверке кода');
        }
    }

    validateOrderForm(data) {
        let isValid = true;
        
        // Очистка предыдущих ошибок
        document.querySelectorAll('.error').forEach(el => {
            el.classList.remove('error');
        });
        document.querySelectorAll('.error-message').forEach(el => {
            el.remove();
        });

        // Валидация имени
        if (!data.name || data.name.trim().length < 2) {
            this.showFieldError('name', 'Имя должно содержать минимум 2 символа');
            isValid = false;
        }

        // Валидация телефона
        const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
        if (!data.phone || !phoneRegex.test(data.phone)) {
            this.showFieldError('phone', 'Введите корректный номер телефона');
            isValid = false;
        }

        // Валидация email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!data.email || !emailRegex.test(data.email)) {
            this.showFieldError('email', 'Введите корректный email');
            isValid = false;
        }

        // Валидация услуги
        if (!data.service) {
            this.showFieldError('service', 'Выберите тип услуги');
            isValid = false;
        }

        return isValid;
    }

    showFieldError(fieldName, message) {
        const field = document.getElementById(fieldName);
        field.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    showModal(modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Фокус на первое поле ввода
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    hideModal(modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }

    showCodeInput() {
        document.getElementById('confirmation-code').value = '';
        this.showModal(this.codeModal);
    }

    showSuccess() {
        this.showModal(this.successModal);
    }
    
    showWaitingForConfirmation(code) {
        // Обновляем сообщение в окне загрузки
        const loadingContent = this.loadingModal.querySelector('.loading-content');
        loadingContent.innerHTML = `
            <div class="spinner"></div>
            <h3>Ожидаем подтверждения...</h3>
            <p>Ваш код: <strong>${code}</strong></p>
            <p>Код отправлен администратору для проверки.</p>
        `;
        this.showModal(this.loadingModal);
    }

    showError(message) {
        alert(message); // В реальном проекте лучше использовать красивые уведомления
    }

    resetAll() {
        // Скрываем все модальные окна
        [this.orderModal, this.loadingModal, this.codeModal, this.successModal].forEach(modal => {
            this.hideModal(modal);
        });
        
        // Очищаем формы
        this.orderForm.reset();
        this.codeForm.reset();
        
        // Очищаем ошибки
        document.querySelectorAll('.error').forEach(el => {
            el.classList.remove('error');
        });
        document.querySelectorAll('.error-message').forEach(el => {
            el.remove();
        });
        
        // Сбрасываем ID заказа
        this.currentOrderId = null;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new OrderManager();
});