#!/usr/bin/env python3

import logging
import socket
import time

from bot.bot_service import Bot
from bot.env import Environments
from bot.log import configure_logger

configure_logger()
logger = logging.getLogger('main')


def main():
    env = Environments.instance()

    mq_host = env.config['MQ_HOST']
    mq_port = env.config['MQ_PORT']
    if not is_reachable_mq(mq_host, mq_port, env.config['MQ_CONNECT_RETRY_COUNT']):
        logger.warning('Could not connect to RabbitMQ.')
        exit(1)

    bot = Bot(env.config['TELEGRAM_BOT_TOKEN'], env.config['MONGO_URI'])
    bot.run()


def is_reachable_mq(mq_host, mq_port, retry_count):
    reachable = False
    retry = 0
    while not reachable and retry < retry_count:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect((mq_host, int(mq_port)))
            reachable = True
            break
        except socket.error:
            logger.warning('RabbitMQ connection should be established. MQ host: {}  port: {}  Retry: {}'
                           .format(mq_host, mq_port, retry + 1))
            time.sleep(1)
            retry += 1
        s.close()
    return reachable


if __name__ == '__main__':
    main()
