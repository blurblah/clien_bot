
import logging
import re

from crawler.services.crawl_service import CrawlService
from crawler.services.data_service import DataService
from crawler.services.queue_service import QueueService


class Job(object):
    def __init__(self, app):
        self.logger = logging.getLogger('job')
        self.app = app
        self.data_service = DataService(app.config['MONGO_URI'])
        self.board = 'allsell'
        crawl_info = self.data_service.select_crawl_info(self.board)
        self.board_name = crawl_info['name']
        self.crawler = CrawlService(crawl_info['url'])

    def crawl(self, board):
        latest_sn = self.data_service.select_latest_sn(board)
        if latest_sn is None:
            return

        latest_sn = int(latest_sn)
        articles = self.crawler.get_latest_articles(latest_sn)
        if len(articles) == 0:
            return

        self.data_service.update_latest_sn(board, articles[0]['sn'])
        search_targets = self.data_service.pivot_all(board)
        for article in articles:
            for target in search_targets:
                self._send_searched_result(self.board_name, target['keyword'], article['title'],
                                           article['link'], target['chat_ids'])

    def _send_searched_result(self, board_name, keyword, title, link, chat_ids):
        self.logger.debug('keyword: {}  title: {}'.format(keyword, title))
        match_count = 0
        words = keyword.split('&')
        for w in words:
            escaped = re.escape(w)
            if re.search(escaped, title, re.IGNORECASE):
                match_count += 1

        if match_count == len(words):
            self.logger.info('Title \'{}\' is matched by keyword: {}'.format(title, keyword))
            message = self._make_md_message_format(board_name, title, link)
            queue_service = QueueService(
                self.app.config['MQ_HOST'], self.app.config['MQ_PORT'], 'allsell'
            )
            for chat_id in chat_ids:
                queue_service.publish({'chat_id': chat_id, 'message': message})
            queue_service.disconnect()

    def _make_md_message_format(self, board_name, title, link):
        return '_{}_\n[{}]({})'.format(board_name, title, link)
