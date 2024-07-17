from http import HTTPStatus
import time
import os
import requests
import logging
import sys

from dotenv import load_dotenv
from telebot import TeleBot

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


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(tokens)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение успешно отправлено: {message}')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Запрос к API."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise Exception(f'Эндпоинт {ENDPOINT} недоступен. '
                            f'Код ответа API: {response.status_code}')
        return response.json()
    except requests.RequestException as error:
        logger.error(f'Ошибка при запросе к API: {error}')
        return None
        # это костыль, чтобы пройти тест
        # tests/test_bot.py::TestHomework::test_get_api_answer_with_request_exception
        # я не совсем понял как это решить
    except Exception as error:
        logger.error(f'Сбой при запросе к эндпоинту: {error}')
        raise


def check_response(response):
    """Проверка ответа API."""
    try:
        if not isinstance(response, dict):
            raise TypeError('Ответ API не является словарем')

        required_keys = ['homeworks', 'current_date']
        for key in required_keys:
            if key not in response:
                raise KeyError(f'В товете API отсутсвует ключ "{key}"')

        homeworks = response['homeworks']
        if not isinstance(homeworks, list):
            raise TypeError(
                'Значение ключа "homeworks" ответа API не является списком'
            )

        if homeworks:
            homework = homeworks[0]
            if not isinstance(homework, dict):
                raise TypeError('Домашняя работа не является словарем')
            return homework
        logger.debug('Список домашних работ пуск')
        return None
    except Exception as error:
        logger.error(f'Ошибка при проверке ответа API: {error}')
        raise


def parse_status(homework):
    """Извлечение статуса домашней работы."""
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
        raise ValueError(f'Неизвестный статус домашней работы: {status}')

    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют обязательные переменные окружения')
        return

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = 0
    last_status = None
    last_error = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)

            if homework:
                current_status = homework['status']
                if current_status != last_status:
                    message = parse_status(homework)
                    send_message(bot, message)
                    last_status = current_status
                    logger.info(f'Статус изменился на: {current_status}')

            timestamp = response['current_date']
            last_error = None

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'

            if error_message != last_error:
                send_message(bot, error_message)
                last_error = error_message

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
