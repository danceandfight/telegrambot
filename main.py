import logging
import os

import requests
import telegram

from environs import Env
from time import sleep

logger = logging.getLogger('ErrorLoger')

class ErrorLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    env = Env()
    env.read_env()

    telegram_bot_token = env('TELEGRAM_BOT_TOKEN')
    telegram_bot_logger_token = env('TELEGRAM_BOT_LOGGER_TOKEN')
    telegram_chat_id = env('TELEGRAM_CHAT_ID')

    bot = telegram.Bot(token=telegram_bot_token)
    bot_logger = telegram.Bot(token=telegram_bot_logger_token)
    
    logger.setLevel(logging.WARNING)
    logger.addHandler(ErrorLogsHandler(bot_logger, telegram_chat_id))

    logging.basicConfig(filename='sample.log', level=logging.INFO)
    url = 'https://dvmn.org/api/long_polling/'
    dvmn_token = env('DVMN_TOKEN')
    headers = {'Authorization': dvmn_token}
    time_stamp = ''
    
    while True:
        try:
            payload = {'timestamp': time_stamp}
            response = requests.get(url, params=payload, headers=headers, timeout=60)
            response.raise_for_status()
            review_results = response.json()
            logger.info(str(review_results))
            if review_results['status'] == 'found':
                time_stamp = int(review_results['last_attempt_timestamp'])
                last_attempt = review_results['new_attempts'][0]
                lesson_title = last_attempt['lesson_title']

                if last_attempt['is_negative']:
                    result = 'К сожалению, в работе нашлись ошибки.'
                elif not last_attempt['is_negative']:
                    result = 'Преподавателю все понравилось, можете приступать к следующему уроку'
                site = 'dvmn.org' + last_attempt['lesson_url']
                message = 'У вас проверили работу "{}"\n\n{}\n\nСсылка на работу: {}\n'.format(lesson_title, result, site)
                bot.send_message(chat_id=telegram_chat_id, text=message)
                time_stamp = ''
            elif review_results['status'] == 'timeout':
                time_stamp = int(review_results['timestamp_to_request'])
            logger.info(str(time_stamp))

        except requests.exceptions.ReadTimeout as err:
            logger.error('Бот упал с ошибкой:')
            logger.error(err)
        except requests.exceptions.ConnectionError as err:
            logger.error('Бот упал с ошибкой:')
            logger.error(err)
            sleep(30)
            

if __name__ == '__main__':
    main()

