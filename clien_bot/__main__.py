#!/usr/bin/env python3

import connexion
import logging
from apscheduler.schedulers.background import BackgroundScheduler

import clien_bot.log
from clien_bot import encoder
from clien_bot.services.bot_service import Bot
from clien_bot.services.crawl_service import CrawlService
from flask_env import Environments
from clien_bot.services.data_service import DataService


def crawl_job(bot_token, mongo_uri):
    crawl_service = CrawlService(mongo_uri)
    articles = crawl_service.get_latest_articles()
    data_service = DataService(mongo_uri)
    search_targets = data_service.pivot_all('allsell')

    for article in articles:
        for target in search_targets:
            if target['keyword'] in article['title']:
                send_message_to_all(bot_token, mongo_uri, target['chat_ids'], article['link'])


def send_message_to_all(bot_token, mongo_uri, chat_ids, message):
    bot = Bot(bot_token, mongo_uri)
    for chat_id in chat_ids:
        bot.send_message(chat_id, message)


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
    bot = Bot(bot_token, mongo_uri)
    bot.run()

    scheduler = BackgroundScheduler()
    scheduler.start()
    logger.info('Background scheduler started.')
    scheduler.add_job(func=crawl_job, trigger='interval', args=[bot_token, mongo_uri], minutes=2, jitter=30)

    app.run(port=8080)

    # 종료시 bot, scheduler 종료 (shutdown 하지 않으면 bot에서 hang 걸림)
    logger.info('Shutdown...')
    bot.shutdown()
    logger.info('Shutdown bot.')
    scheduler.remove_all_jobs()
    scheduler.shutdown(wait=False)
    logger.info('Shutdown scheduler.')


if __name__ == '__main__':
    main()
