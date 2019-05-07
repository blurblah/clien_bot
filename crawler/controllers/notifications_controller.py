import logging

import connexion
from flask import current_app as app

from crawler.models.failure import Failure  # noqa: E501
from crawler.models.notification import Notification  # noqa: E501
from crawler.models.success import Success  # noqa: E501

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
    bot_token = app.config['TELEGRAM_BOT_TOKEN']
    interval = app.config['REPEAT_INTERVAL']
    offset = app.config['INTERVAL_OFFSET']

    # TODO: 문제가 있는 코드. 구조 개선이 필요함
    # bot = Bot(bot_token, mongo_uri, interval, offset)
    # data_service = DataService(mongo_uri)
    # for chat_id in data_service.select_all_chat_ids():
    #     try:
    #         bot.send_message(chat_id, notification.message)
    #     except Exception as e:
    #         logger.error('[{}] Exception. Details: {}'.format(chat_id, str(e)))
    #     # TODO: Spammer 등록 방지용 임시 코드
    #     time.sleep(0.1)

    return Success()
