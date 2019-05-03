#!/usr/bin/env python3

import logging

import connexion
from apscheduler.schedulers.background import BackgroundScheduler

import crawler.log
from crawler import encoder
from crawler.services.job import Job
from flask_env import Environments

crawler.log.configure_logger()
logger = logging.getLogger('main')


def main():
    connecxion_app = connexion.App(__name__, specification_dir='./swagger/')
    app = connecxion_app.app
    env = Environments(app)
    env.from_yaml('config.yml')
    app.json_encoder = encoder.JSONEncoder
    connecxion_app.add_api('swagger.yaml', arguments={'title': 'Clien notification bot'})

    interval = app.config['REPEAT_INTERVAL']
    offset = app.config['INTERVAL_OFFSET']
    board = 'allsell'

    job = Job(app)
    scheduler = BackgroundScheduler()
    scheduler.add_job(job.crawl, 'interval', args=[board],
                      seconds=interval, jitter=offset)
    scheduler.start()
    connecxion_app.run(port=8080)


if __name__ == '__main__':
    main()
