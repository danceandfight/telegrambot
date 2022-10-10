import logging
import os

import requests
import telegram

from environs import Env

env = Env()
env.read_env()

TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_LOGGER_TOKEN = env('TELEGRAM_BOT_LOGGER_TOKEN')
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
bot_logger = telegram.Bot(token=TELEGRAM_BOT_LOGGER_TOKEN)

class ErrorLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    logging.basicConfig(filename='sample.log', level=logging.INFO)
    url = 'https://dvmn.org/api/long_polling/'
    DVMN_TOKEN = env('DVMN_TOKEN')
    headers = {'Authorization': DVMN_TOKEN}
    time_stamp = ''
    
    while True:
        try:
            payload = {'timestamp': time_stamp}
            response = requests.get(url, params=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise requests.exceptions.HTTPError(response['error'])
            logger.info(str(data))
            if data['status'] == 'found':
                time_stamp = int(data['last_attempt_timestamp'])
                response_info = data['new_attempts'][0]
                lesson_title = response_info['lesson_title']

                if response_info['is_negative']:
                    result = 'К сожалению, в работе нашлись ошибки.'
                elif not response_info['is_negative']:
                    result = 'Преподавателю все понравилось, можете приступать к следующему уроку'
                site = 'dvmn.org' + response_info['lesson_url']
                message = 'У вас проверили работу "{}"\n\n{}\n\nСсылка на работу: {}\n'.format(lesson_title, result, site)
                bot.send_message(chat_id='209706595', text=message)
                time_stamp = ''

            elif data['status'] == 'timeout':
                time_stamp = int(data['timestamp_to_request'])
            logger.info(str(time_stamp))

        except Exception as err:
            logger.error('Бот упал с ошибкой:')
            logger.error(err)

if __name__ == '__main__':
    logger = logging.getLogger('ErrorLoger')
    logger.setLevel(logging.WARNING)
    logger.addHandler(ErrorLogsHandler(bot_logger, '209706595'))
    main()

