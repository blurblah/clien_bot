#!/usr/bin/env python3

import connexion
import logging

import clien_bot.log
from clien_bot import encoder
from clien_bot.services.bot_service import Bot
from flask_env import Environments


def main():
    clien_bot.log.configure_logger()
    logger = logging.getLogger('main')
    app = connexion.App(__name__, specification_dir='./swagger/')
    env = Environments(app.app)
    env.from_yaml('config.yml')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Clien notification bot'})

    mongo_uri = app.app.config['MONGO_URI']
    bot_token = app.app.config['TELEGRAM_BOT_TOKEN']
    interval = app.app.config['REPEAT_INTERVAL']
    offset = app.app.config['INTERVAL_OFFSET']
    bot = Bot(bot_token, mongo_uri, interval, offset)
    bot.run()

    app.run(port=8080)

    # 종료시 bot, scheduler 종료 (shutdown 하지 않으면 bot에서 hang 걸림)
    logger.info('Shutdown...')
    bot.shutdown()
    logger.info('Shutdown bot.')


if __name__ == '__main__':
    main()
