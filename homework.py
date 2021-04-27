import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

FORMATTER = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


class CustomHandler(logging.Handler):
    def emit(self, record):
        if record.levelname != 'ERROR' or record.levelname != 'CRITICAL':
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
    homework_name = homework['homework_name'].split('__')[-1].split('.')[0]
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось,'
                   ' можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    params = {
        'from_date': current_timestamp,
    }
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        params=params,
        headers=headers,
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


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
                logger.info('Message sent!')
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
