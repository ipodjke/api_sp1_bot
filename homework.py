import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import TelegramError

load_dotenv()

URL = 'https://praktikum.yandex.ru/'
API = 'api/'
SERVICE = 'user_api/'
DATA = 'homework_statuses/'

COOLDOWN_QUERY = 1200
SLEEP_TIME_ERROR = 5
try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError as err:
    exit(f'Отсутствует значение переменной: {err}')

FORMATTER = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


class CustomHandler(logging.Handler):
    def emit(self, record):
        if record.levelname != 'ERROR':
            return None
        text = (f'{record.asctime}, {record.levelname},'
                f' {record.name}, {record.message}')
        url = (f'https://api.telegram.org/bot{TELEGRAM_TOKEN}'
               f'/sendMessage?chat_id={CHAT_ID}&text={text}')
        return requests.get(url)


logger = logging.getLogger(f'{__name__}__base_logger')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(FORMATTER)
logger.addHandler(handler)
logger.addHandler(CustomHandler())

logger.propagate = False


def parse_homework_status(homework):
    name = homework.get('homework_name')
    if not name:
        logger.debug('Homework have no homework_name key')
        return None
    name = name.split('__')[-1].split('.')[0]
    status_messages = {
        'rejected': (f'У вас проверили работу "{name}"!\n\n'
                     'К сожалению в работе нашлись ошибки.'),
        'approved': (f'У вас проверили работу "{name}"!\n\n'
                     'Ревьюеру всё понравилось, можно приступать к'
                     ' следующему уроку.'),
        'reviewing': f'Ревьювер принял "{name}" на рассмотрение.',
    }
    result = status_messages.get(homework.get('status'))
    if not result:
        logger.debug('Homework wrong status key')
        return None
    return result


def get_homework_statuses(current_timestamp):
    params = {
        'from_date': current_timestamp,
    }
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    homework_statuses = requests.get(
        '{}{}{}{}'.format(URL, API, SERVICE, DATA),
        params=params,
        headers=headers,
    )
    if homework_statuses is None:
        logger.debug("Cann't do request.get for homework_statuses")
        homework_statuses = {}
    return homework_statuses.json()


def send_message(message, bot_client):
    if message is None:
        logger.debug("Message don't send because message is None!")
    try:
        result = bot_client.send_message(chat_id=CHAT_ID, text=message)
        logger.info('Message send!')
        return result
    except TelegramError as e:
        logger.error(f'Ошибка отправки телеграмм: {e}')


def main():
    current_timestamp = int(time.time())
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Bot started!')
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(COOLDOWN_QUERY)
        except Exception as e:
            logger.error(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(SLEEP_TIME_ERROR)


if __name__ == '__main__':
    main()
