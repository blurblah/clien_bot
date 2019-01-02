
import json
import logging
import requests
from bs4 import BeautifulSoup

from clien_bot.services.data_service import DataService


class CrawlService(object):
    def __init__(self, mongo_uri):
        self.ENDPOINT = 'https://www.clien.net'
        self.logger = logging.getLogger('crawler')
        self.data_service = DataService(mongo_uri)
        # 게시판 종류는 우선 하나만
        self.board = 'allsell'

    def get_latest_articles(self):
        articles = []
        crawl_info = self.data_service.select_crawl_info(self.board)
        latest_sn = int(crawl_info['latest_sn'])
        self.logger.info('latest sn: {}'.format(latest_sn))
        page = 0
        while True:
            extracted = self._extract_articles(
                self._make_url_with_page(crawl_info['url'], page),
                latest_sn)
            articles.extend(extracted)
            if latest_sn == 0:
                break
            if extracted[-1]['sn'] <= latest_sn:
                del articles[-1]
                break
            else:
                page = page + 1
        if len(articles) > 0:
            self.data_service.update_latest_sn(self.board, articles[0]['sn'])

        for article in articles:
            self.logger.info(json.dumps(article, ensure_ascii=False))
        return articles

    def _extract_article_info(self, tag):
        try:
            serial_number = int(tag['data-board-sn'])
            title_tag = tag.find('a', attrs={'class': 'list_subject'})
            link = title_tag['href']
            title = title_tag.find('span', attrs={'data-role': 'list-title-text'}).text
            return {
                'sn': serial_number,
                'title': title,
                'link': '{}{}'.format(self.ENDPOINT, link)
            }
        except Exception as e:
            self.logger.error(str(e))
            return None

    def _make_url_with_page(self, base_url, page=0):
        return '{}?od=T31&po={}'.format(base_url, page)

    def _extract_articles(self, url, latest_sn):
        articles = []
        r = requests.get(url)
        r.encoding = 'UTF-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('div', attrs={'data-role': 'list-row'})
        for item in items:
            article = self._extract_article_info(item)
            if article is None:
                continue
            articles.append(article)
            if article['sn'] <= latest_sn:
                break
        return articles
