import connexion
import six

from clien_bot.models.failure import Failure  # noqa: E501
from clien_bot.models.notification import Notification  # noqa: E501
from clien_bot.models.success import Success  # noqa: E501
from clien_bot import util


def notifications_post(body):  # noqa: E501
    """notifications_post

    모든 사용자에게 공지 메세지 발송 # noqa: E501

    :param body: 메세지 내용
    :type body: dict | bytes

    :rtype: Success
    """
    if connexion.request.is_json:
        body = Notification.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
