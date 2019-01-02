
import logging
import telegram
from telegram.ext import Updater, CommandHandler
from clien_bot.services.data_service import DataService


class Bot(object):
    def __init__(self, token, mongo_uri):
        self.logger = logging.getLogger('bot')
        self.__bot = telegram.Bot(token=token)
        self.updater = Updater(bot=self.__bot)
        self.dispatcher = self.updater.dispatcher
        self.add_handler('start', self.start_bot)
        self.add_handler('register', self.register_keywords, has_args=True)
        self.add_handler('list', self.show_registered_keywords)
        self.add_handler('stop', self.stop_bot)
        #self.add_handler('unregister', self.unregister_keywords, has_args=True)
        self.add_handler('clear', self.clear)
        self.service = DataService(mongo_uri)
        # 게시판 종류는 우선 하나만
        self.board = 'allsell'

    def add_handler(self, command, callback, has_args=False):
        handler = CommandHandler(command, callback, pass_args=has_args)
        self.dispatcher.add_handler(handler)
        self.logger.info('Registered handler for command {}.'.format(command))

    def start_bot(self, bot, update):
        chat_id = update.message.chat_id
        # chat_id DB 저장 (공지 발송용)
        inserted = self.service.insert_new_chat_id(chat_id)
        self.logger.info('[{}] Bot registered. inserted_id: {}'.format(chat_id, inserted))
        update.message.reply_text('이거슨 클리앙 알리미.')
        # TODO: 기본 설명 추가

    def register_keywords(self, bot, update, args):
        chat_id = update.message.chat_id
        str_args = ' '.join(args)
        self.logger.info('[{}] Input arguments: {}'.format(chat_id, str_args))
        # chat_id, keywords DB 저장
        updated = self.service.update_keywords(chat_id, self.board, args)
        self.logger.info('[{}] Updated id: {}'.format(chat_id, updated))
        self.logger.info('[{}] Registered keywords: {}'.format(chat_id, str_args))
        update.message.reply_text('Registered keywords: {}'.format(str_args))

    '''
    def unregister_keywords(self, bot, update, args):
        chat_id = update.message.chat_id
        str_args = ' '.join(args)
        self.logger.info('[{}] Input arguments: {}'.format(chat_id, str_args))
        # TODO: keywords를 DB에서 제거
        self.logger.info('[{}] Unregistered keywords: {}'.format(chat_id, args))
        # TODO: 남은 keyword list DB에서 가져오기
        registered = []
        update.message.reply_text('Registered keywords: {}'.format(registered))
    '''

    def clear(self, bot, update):
        chat_id = update.message.chat_id
        # chat_id의 모든 keywords를 DB에서 제거
        updated = self.service.clear_keywords(chat_id, self.board)
        self.logger.info('[{}] Updated id: {}'.format(chat_id, updated))
        self.logger.info('[{}] Unregistered all keywords'.format(chat_id))
        # keyword list DB에서 가져오기
        registered = self.service.select_keywords(chat_id, self.board)
        # TODO: 리스트가 그대로 표시됨
        update.message.reply_text('Registered keywords: {}'.format(registered))

    def show_registered_keywords(self, bot, update):
        chat_id = update.message.chat_id
        # DB에서 chat_id로 등록된 keyword list 가져오기
        keywords = self.service.select_keywords(chat_id, self.board)
        # TODO: 리스트가 그대로 표시됨
        self.logger.info('[{}] Registered keywords: {}'.format(chat_id, keywords))
        if len(keywords) > 0:
            msg = 'Registered keywords: {}'.format(keywords)
        else:
            msg = '저장된 검색 키워드가 없습니다!'
        update.message.reply_text(msg)

    def send_message(self, chat_id, msg):
        self.__bot.send_message(chat_id=chat_id, text=msg)
        self.logger.info('[{}] Sent message.'.format(chat_id))

    def stop_bot(self, bot, update):
        chat_id = update.message.chat_id
        # DB에서 사용자 제거
        self.service.delete_chat_id(chat_id)
        self.logger.info('[{}] Bot unregistered.'.format(chat_id))

    def shutdown(self):
        self.updater.stop()
        self.updater.idle = False

    def run(self):
        self.updater.start_polling()
        self.logger.info('Start polling...')
