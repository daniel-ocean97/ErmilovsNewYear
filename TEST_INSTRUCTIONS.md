# Инструкция по запуску тестов Celery

## Шаг 1: Убедитесь, что Redis запущен

```bash
# Windows (если установлен через установщик)
redis-server

# Или через Docker
docker run -d -p 6379:6379 redis
```

## Шаг 2: Запустите Celery Worker

Откройте **первый терминал** и запустите:

```bash
# Вариант 1: Через скрипт
python run_celery_worker.py

# Вариант 2: Через команду Celery
celery -A celery_app worker -l info
```

Вы должны увидеть что-то вроде:
```
[INFO/MainProcess] celery@... ready.
```

## Шаг 3: Запустите тесты

Откройте **второй терминал** и запустите:

```bash
python run_test.py
```

## Что происходит:

1. `send_test_message` - отправляет одно тестовое сообщение в Telegram
2. `test_pair` - отправляет 3 тестовых сообщения с задержкой

## Проверка результатов:

- Смотрите логи в терминале с worker
- Проверьте Telegram - должны прийти сообщения
- В терминале с тестами увидите результаты выполнения

## Устранение проблем:

### Ошибка "Connection refused" или "Cannot connect to Redis"
- Убедитесь, что Redis запущен: `redis-cli ping` (должен ответить `PONG`)

### Ошибка "No module named 'celery_app'"
- Убедитесь, что вы запускаете из директории `ErmilovsNewYear`

### Задачи не выполняются
- Проверьте, что worker запущен и видит задачи
- Проверьте логи worker на наличие ошибок

### Сообщения не приходят в Telegram
- Проверьте `BOT_TOKEN` в `.env` файле
- Проверьте `TEST_CHAT_ID` в `celery_test.py` (должен быть ваш Telegram ID)

