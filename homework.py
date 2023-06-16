import os
import logging
import requests
import telegram
import time
import sys

from http import HTTPStatus

from exceptions import AbsenceVariables

from logging import StreamHandler, FileHandler

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
            return False
    logger.info('Переменные окружения доступ')
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
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        logger.error(f'Не ожидаемый HTTP статус {response.status_code}')
        raise Exception(f'Не ожидаемый HTTP статус {response.status_code}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие данных."""
    if not isinstance(response, dict):
        logger.error('Не соответствует типу данных')
        raise TypeError('Не соответствует типу данных')

    keys = ('current_date', 'homeworks')

    for key in response:
        if key not in keys:
            logger.error('Отсутствует данные в API')
            return False

    homework = response.get('homeworks')

    if not isinstance(homework, list):
        logger.error('Не соответствует типу данных')
        raise TypeError('Не соответствует типу данных')

    if not homework:
        logger.error('Отсутствуют данные в homework')
        return False

    return True


def parse_status(homework):
    """Извлекает из конкретной домашней работы, статус этой работы."""
    if 'homework_name' not in homework:
        logger.error('Отсутствуют ключ ')
        raise KeyError('Отсутсвует ключ ')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error(f'Отсутствует статус работы {homework_status}')
        raise ValueError(f'Отсутствует статус работы {homework_status}')
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{HOMEWORK_VERDICTS[homework_status]}'
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise AbsenceVariables('Отсутствует токен')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    # timestamp = int(time.time())
    while True:
        try:
            response_api = get_api_answer(timestamp)
            if check_response(response_api):
                message = parse_status(response_api['homeworks'][0])
                send_message(bot, message)
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
