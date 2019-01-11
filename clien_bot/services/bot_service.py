
import logging
import random
import re
import telegram
from functools import wraps
from telegram.ext import Updater, CommandHandler

from clien_bot.services.crawl_service import CrawlService
from clien_bot.services.data_service import DataService


class Bot(object):

    class Decorators(object):
        @classmethod
        def send_typing_action(cls, func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                instance, bot, update = args
                bot.send_chat_action(chat_id=update.effective_message.chat_id,
                                     action=telegram.ChatAction.TYPING)
                return func(instance, bot, update, **kwargs)
            return wrapper

    def __init__(self, token, mongo_uri, repeat_interval, interval_offset):
        self.logger = logging.getLogger('bot')
        self.__bot = telegram.Bot(token=token)
        self.updater = Updater(bot=self.__bot)
        self.dispatcher = self.updater.dispatcher
        self.add_handler('start', self.start_bot)
        self.add_handler('register', self.register_keywords, has_args=True)
        self.add_handler('list', self.show_registered_keywords)
        self.add_handler('stop', self.stop_bot)
        self.add_handler('clear', self.clear)
        self.add_handler('help', self.help)
        self.data_service = DataService(mongo_uri)
        # 게시판 종류는 우선 하나만
        self.board = 'allsell'
        self.crawl_service = CrawlService(mongo_uri)
        self.repeat_interval = repeat_interval
        self.interval_offset = interval_offset
        self._add_job_to_queue(self.crawl_job_cb, self.repeat_interval, self.interval_offset)

    def add_handler(self, command, callback, has_args=False):
        handler = CommandHandler(command, callback, pass_args=has_args)
        self.dispatcher.add_handler(handler)
        self.logger.info('Registered handler for command {}.'.format(command))

    @Decorators.send_typing_action
    def start_bot(self, bot, update):
        chat_id = update.message.chat_id
        # chat_id DB 저장 (공지 발송용)
        inserted = self.data_service.insert_new_chat_id(chat_id)
        self.logger.info('[{}] Bot registered. inserted_id: {}'.format(chat_id, inserted))
        welcome_lines = [
            '클리앙 알리미 봇입니다.',
            '현재는 사고팔고 게시판에 대해서만 서비스가 가능합니다.'
        ]
        update.message.reply_text('\n'.join(welcome_lines))
        self.send_message(chat_id, self._make_help_message(), telegram.ParseMode.MARKDOWN)

    @Decorators.send_typing_action
    def register_keywords(self, bot, update, args):
        chat_id = update.message.chat_id
        str_args = ' '.join(args)
        self.logger.info('[{}] Input arguments: {}'.format(chat_id, str_args))
        # chat_id, keywords DB 저장
        updated = self.data_service.update_keywords(chat_id, self.board, args)
        self.logger.info('[{}] Updated id: {}'.format(chat_id, updated))
        self.logger.info('[{}] Registered keywords: {}'.format(chat_id, str_args))
        update.message.reply_text('Registered keywords: {}'.format(str_args))

    @Decorators.send_typing_action
    def clear(self, bot, update):
        chat_id = update.message.chat_id
        # chat_id의 모든 keywords를 DB에서 제거
        updated = self.data_service.clear_keywords(chat_id, self.board)
        self.logger.info('[{}] Updated id: {}'.format(chat_id, updated))
        self.logger.info('[{}] Unregistered all keywords'.format(chat_id))
        # keyword list DB에서 가져오기
        registered = self.data_service.select_keywords(chat_id, self.board)
        # TODO: 리스트가 그대로 표시됨
        update.message.reply_text('Registered keywords: {}'.format(registered))

    @Decorators.send_typing_action
    def show_registered_keywords(self, bot, update):
        chat_id = update.message.chat_id
        # DB에서 chat_id로 등록된 keyword list 가져오기
        keywords = self.data_service.select_keywords(chat_id, self.board)
        # TODO: 리스트가 그대로 표시됨
        self.logger.info('[{}] Registered keywords: {}'.format(chat_id, keywords))
        if len(keywords) > 0:
            msg = 'Registered keywords: {}'.format(keywords)
        else:
            msg = '저장된 검색 키워드가 없습니다!'
        update.message.reply_text(msg)

    @Decorators.send_typing_action
    def help(self, bot, update):
        chat_id = update.message.chat_id
        self.logger.info('[{}] Help message requested.'.format(chat_id))
        update.message.reply_text(self._make_help_message(), parse_mode=telegram.ParseMode.MARKDOWN)

    def send_message(self, chat_id, msg, parse_mode=None):
        self.__bot.send_message(chat_id=chat_id, text=msg, parse_mode=parse_mode)
        self.logger.info('[{}] Sent message.'.format(chat_id))

    def stop_bot(self, bot, update):
        chat_id = update.message.chat_id
        # DB에서 사용자 제거
        self.data_service.delete_chat_id(chat_id)
        self.logger.info('[{}] Bot unregistered.'.format(chat_id))

    def shutdown(self):
        self.updater.stop()
        self.updater.idle = False

    def run(self):
        self.updater.start_polling()
        self.logger.info('Start polling...')

    def _add_job_to_queue(self, cb, interval, first=0):
        job_queue = self.updater.job_queue
        return job_queue.run_repeating(cb, interval=interval, first=first)

    # TODO: API로 job 제거할 때 사용 예정
    def _remove_job(self, job):
        job.schedule_removal()

    def crawl_job_cb(self, bot, job):
        articles = self.crawl_service.get_latest_articles(self.board)
        # TODO: DB 관련된 작업을 정리할 필요가 있음
        search_targets = self.data_service.pivot_all(self.board)
        board_name = self.data_service.select_crawl_info(self.board)['name']

        for article in articles:
            for target in search_targets:
                self._send_searched_result(board_name, target['keyword'], article['title'],
                                           article['link'], target['chat_ids'])
        offset = random.randint(-self.interval_offset, self.interval_offset)
        job.interval = self.repeat_interval + offset
        self.logger.info('Crawl job will be triggered after {} seconds'.format(job.interval))

    def _send_searched_result(self, board_name, keyword, title, link, chat_ids):
        if re.search(keyword, title, re.IGNORECASE):
            message = self._make_md_message_format(board_name, title, link)
            for chat_id in chat_ids:
                self.send_message(chat_id, message, telegram.ParseMode.MARKDOWN)

    def _make_md_message_format(self, board_name, title, link):
        return '_{}_\n[{}]({})'.format(board_name, title, link)

    def _make_help_message(self):
        help_lines = [
            '<클리앙 알리미 도움말>',
            '*/start* : 시작',
            '*/register* : 키워드 등록',
            '  _/register 키워드1 키워드2 ..._',
            '  _참고 : 이미 등록한 키워드 리스트가 있다면 일괄 교체합니다._',
            '*/list* : 등록한 키워드 리스트 표시',
            '*/clear* : 등록 키워드 전체 삭제',
            '*/help* : 도움말 표시',
            '문의사항이 있다면 *blurblah@blurblah.net*으로 연락주세요.'
        ]
        return '\n'.join(help_lines)
