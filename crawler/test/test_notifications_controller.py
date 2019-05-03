# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from crawler.models.failure import Failure  # noqa: E501
from crawler.models.notification import Notification  # noqa: E501
from crawler.models.success import Success  # noqa: E501
from crawler.test import BaseTestCase


class TestNotificationsController(BaseTestCase):
    """NotificationsController integration test stubs"""

    def test_notifications_post(self):
        """Test case for notifications_post

        
        """
        body = Notification()
        response = self.client.open(
            '/clienbot/v1/notifications',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
