import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiException

from exceptions import APIResponseError, HomeworkStatusError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = ("PRACTICUM_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID")
    missing_tokens = []

    for token in tokens:
        if not globals().get(token):
            missing_tokens.append(token)

    if missing_tokens:
        missing_tokens = ", ".join(missing_tokens)
        error_message = (f"Отсутствуют обязательные переменные окружения: "
                         f"{missing_tokens}")
        logging.critical(error_message)
        sys.exit(1)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        logger.debug(f'Начало отправки сообщения: {message}')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение успешно отправлено: {message}')
    except (ApiException, requests.RequestException) as error:
        logger.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Запрос к API."""
    params = {'from_date': timestamp}
    logger.debug(f"Отправка запроса к API: {ENDPOINT}. Параметры: {params}")

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка при запросе к API: {error}')

    if response.status_code != HTTPStatus.OK:
        error_message = (
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}. '
            f'Причина: {response.reason}'
        )
        raise APIResponseError(error_message)

    logger.debug(f"Успешный ответ от API: {ENDPOINT}")

    return response.json()


def check_response(response):
    """Проверка ответа API."""
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ API не является словарем. '
            f'Получен {type(response)}'
        )

    required_keys = ['homeworks', 'current_date']
    for key in required_keys:
        if key not in response:
            raise KeyError(f'В товете API отсутсвует ключ "{key}"')

    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            'Значение ключа "homeworks" ответа API не является списком. '
            f'Получен {type(response)}'
        )

    if homeworks and not isinstance(homeworks[0], dict):
        raise TypeError(
            'Домашняя работа не является словарем. '
            f'Получен {type(homeworks[0])}'
        )

    return homeworks


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    logger.debug('Начало проверки статуса домашней работы.')

    if 'homework_name' not in homework:
        raise KeyError(
            'В ответе API домашней работы отсутствует ключ "homework_name"'
        )
    if 'status' not in homework:
        raise KeyError(
            'В ответе API домашней работы отсутствует ключ "status"'
        )

    homework_name = homework['homework_name']
    status = homework['status']

    if status not in HOMEWORK_VERDICTS:
        raise HomeworkStatusError(
            f'Неизвестный статус домашней работы: {status}'
        )

    verdict = HOMEWORK_VERDICTS[status]

    logger.debug('Проверка статуса домашней работы завершена успешно.')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = 0
    last_error = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)

            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
                logger.info(f'Статус изменился на: {message}')
                last_error = None
            else:
                logger.debug('Отсутствие новых статусов')

            timestamp = response.get('current_date', int(time.time()))

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'

            if error_message != last_error:
                send_message(bot, error_message)
                last_error = error_message

            logger.error(error_message, exc_info=True)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(asctime)s - '
            '%(name)s - '
            '%(levelname)s - '
            '%(filename)s:'
            '%(funcName)s:'
            '%(lineno)d - '
            '%(message)s'
        ),
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    main()
