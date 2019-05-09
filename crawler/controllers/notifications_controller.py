import logging

import connexion
from flask import current_app as app

from crawler.models.failure import Failure  # noqa: E501
from crawler.models.notification import Notification  # noqa: E501
from crawler.models.success import Success  # noqa: E501
from crawler.services.data_service import DataService
from crawler.services.queue_service import QueueService
import time

logger = logging.getLogger('controller')


def notifications_post(body):  # noqa: E501
    """notifications_post

    모든 사용자에게 공지 메세지 발송 # noqa: E501

    :param body: 메세지 내용
    :type body: dict | bytes

    :rtype: Success
    """
    if connexion.request.is_json and 'message' in body:
        notification = Notification.from_dict(body)
    else:
        logger.warning('Invalid parameters: {}'.format(body))
        return Failure('Invalid parameters', 400)

    mongo_uri = app.config['MONGO_URI']
    data_service = DataService(mongo_uri)
    queue_service = QueueService(
        app.config['MQ_HOST'], app.config['MQ_PORT'], 'allsell'
    )
    for chat_id in data_service.select_all_chat_ids():
        queue_service.publish({'chat_id': chat_id, 'message': notification.message})
        # TODO: Spammer 등록 방지용 임시 코드
        time.sleep(0.1)
    queue_service.disconnect()

    return Success()
