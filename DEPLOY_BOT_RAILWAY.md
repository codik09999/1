# Деплой Telegram бота на Railway

## Шаги для деплоя:

### 1. Подготовка кода
Убедитесь что у вас есть файлы:
- `bot.py` - основной код бота
- `Dockerfile.bot` - Docker конфигурация  
- `requirements.txt` - зависимости Python

### 2. Создание нового Railway проекта для бота

1. Зайдите на https://railway.app/
2. Нажмите "New Project" 
3. Выберите "Deploy from GitHub repo"
4. Выберите репозиторий `codik09999/1` (или создайте новый)
5. В настройках проекта:

### 3. Настройка переменных окружения

В Railway проекте установите переменные:

```
BOT_TOKEN=7808830885:AAHFkGTaOylnQ99RrNolU5UgjEgo2gxFrqo
WEB_SERVER_URL=https://web-production-d0b17.up.railway.app
ADMIN_CHAT_ID=2063086506
```

### 4. Настройка сборки

В Railway проекте:
1. Перейдите в Settings -> Build
2. Укажите Dockerfile: `Dockerfile.bot`
3. Или создайте `railway.toml`:

```toml
[build]
builder = "dockerfile" 
dockerfilePath = "Dockerfile.bot"

[deploy]
startCommand = "python bot.py"
```

### 5. Деплой

1. Railway автоматически задеплоит бота
2. Проверьте логи в Dashboard
3. Бот должен запуститься и начать работать

### 6. Тестирование

1. Отправьте `/start` в Telegram бот
2. Создайте тестовый заказ через сайт
3. Проверьте что уведомление приходит
4. Нажмите "📱 Отправить SMS" - должно показать "✅ SMS ОТПРАВЛЕН!"

## Примечания

- Убедитесь что старый бот остановлен, чтобы избежать конфликтов
- Логи бота можно смотреть в Railway Dashboard  
- При изменениях в коде, Railway автоматически пересобирает бота