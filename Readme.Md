Запуск бота

# Конфигурация

.env
Нужны ключи yandex_waether_api, tg-bot-token.
Формат .sample.env

# Запуск

## Создаем вирутальное окружение

```
python -m venv .venv
```

## Установить зависимости

```
pip instal -r requirements.txt
```

## Активировать виртуальное окружение

```
cmd .\.venv\Scripts\activate
```

## Запуск бота

```
python bot.py
```
