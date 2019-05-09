#!/usr/bin/env python3

import logging
import socket
import time

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

    if not is_reachable_mq(app.config['MQ_HOST'], app.config['MQ_PORT'],
                           app.config['MQ_CONNECT_RETRY_COUNT']):
        logger.warning('Could not connect to RabbitMQ.')
        exit(1)

    interval = app.config['REPEAT_INTERVAL']
    offset = app.config['INTERVAL_OFFSET']
    board = 'allsell'

    job = Job(app)
    scheduler = BackgroundScheduler()
    scheduler.add_job(job.crawl, 'interval', args=[board],
                      seconds=interval, jitter=offset)
    scheduler.start()
    connecxion_app.run(port=8080)


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
