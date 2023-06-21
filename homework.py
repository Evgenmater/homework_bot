import logging
import os
import sys
import time

import requests
import telegram

import exceptions

from http import HTTPStatus
from logging import FileHandler, StreamHandler

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_TG')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

file_handler = FileHandler('main.log', encoding='UTF-8', mode='w')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    environment_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for name, var in environment_variables.items():
        if not var:
            logger.critical(
                f'Отсутствие обязательных переменных окружения {name}'
            )
    for name, var in environment_variables.items():
        if not var:
            return False
    logger.info('Переменные окружения доступны')
    return True


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
    logger.debug('Удачная отправка сообщения в Telegram')


def get_api_answer(timestamp):
    """Делает запрос к API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        logger.info(
            f'Параметры переданные при запросе: Url - {ENDPOINT}; '
            f'Авторизация - {HEADERS}; Метка времени {payload}.'
        )
    except Exception as error:
        raise exceptions.MainRequest(
            f'Ошибка при запросе к основному API: {error}'
        )
    if response.status_code != HTTPStatus.OK:
        raise requests.RequestException(
            f'Не ожидаемый HTTP статус {response.status_code}'
        )
    try:
        return response.json()
    except ValueError:
        raise exceptions.DecodingFailed('Не удалось расшифровать JSON')


def check_response(response):
    """Проверяет ответ API на соответствие данных."""
    if not isinstance(response, dict):
        raise exceptions.TypeErrorDict(
            'При запросе в формате JSON переданные в response'
            ' данные не соответствую типу в виде словаря'
        )

    keys = ('current_date', 'homeworks')

    for key in response:
        if key not in keys:
            raise exceptions.MissingDataDict(
                'Отсутствуют данные "current_date" или "homeworks" в API'
            )

    homework = response.get('homeworks')

    if not isinstance(homework, list):
        raise exceptions.TypeErrorList(
            'Значение ключа homeworks '
            'не соответствуют типу данных в виде списка'
        )

    return True


def parse_status(homework):
    """Извлекает из конкретной домашней работы, статус этой работы."""
    if not isinstance(homework, dict):
        raise exceptions.HomeworkErrorDict(
            'Данные переданные в параметр homework '
            'не соответствую типу в виде словаря'
        )
    if 'homework_name' not in homework:
        raise exceptions.HomeworkKey(
            'В словаре homework отсутсвует ключ homework_name'
        )
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error(f'Отсутствует статус работы {homework_status}')
        raise exceptions.HomeworkStatus(
            f'Отсутствует статус работы {homework_status}'
        )
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{HOMEWORK_VERDICTS[homework_status]}'
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise exceptions.AbsenceVariables('Отсутствует токен')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            timestamp = int(time.time())
            response_api = get_api_answer(timestamp)
            if check_response(response_api):
                message = parse_status(response_api['homeworks'][0])
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = int(time.time())


if __name__ == '__main__':
    main()
