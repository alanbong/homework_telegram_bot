![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

Библиотеки: `pyTelegramBotAPI`, `python-dotenv`

# Телеграмм бот для проверки статуса домашней работы на сервисе Яндекс.Практикум

Проект отслеживает статус домашней работы на Яндекс.Практикуме через API и отправляет уведомления в Telegram. Для удобства ведётся лог работы, а все ключи хранятся в .env-файле с использованием dotenv.

Статус работы может быть:

* Принято (approved)
* Ожидает проверки (reviewing)
* Есть правки (rejected)

Если статус поменялся программа уведомляет об этом пользователя путем отправки сообщения в телеграмм.

#### Клонировать репозиторий и перейти в него в командной строке:

> git clone https://github.com/alanbong/homework_telegram_bot.git

#### Установите и активируйте виртуальное окружение

> python -m venv venv

> source venv/bin/activate

#### Установите зависимости из файла requirements.txt

> pip install -r requirements.txt

#### Запустите программу

> python3 manage.py runserver
