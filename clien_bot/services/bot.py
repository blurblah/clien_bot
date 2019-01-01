
import logging
import telegram
from telegram.ext import Updater, CommandHandler


class Bot(object):
    def __init__(self, token):
        self.logger = logging.getLogger('bot')
        self.__bot = telegram.Bot(token=token)
        self.updater = Updater(bot=self.__bot)
        self.dispatcher = self.updater.dispatcher
        self.register_handler('start', self.start_bot)
        self.register_handler('register', self.register_keywords, has_args=True)
        self.register_handler('list', self.show_registered_keywords)
        self.register_handler('stop', self.stop_bot)
        self.register_handler('unregister', self.unregister_keywords, has_args=True)
        self.register_handler('clear', self.clear)

    def register_handler(self, command, callback, has_args=False):
        handler = CommandHandler(command, callback, pass_args=has_args)
        self.dispatcher.add_handler(handler)
        self.logger.info('Registered handler for command {}.'.format(command))

    def start_bot(self, bot, update):
        chat_id = update.message.chat_id
        # TODO: chat_id DB 저장 (공지 발송용)
        self.logger.info('[{}] Bot registered.'.format(chat_id))
        update.message.reply_text('이거슨 클리앙 알리미.')
        # TODO: 기본 설명 추가

    def register_keywords(self, bot, update, args):
        chat_id = update.message.chat_id
        str_args = ' '.join(args)
        self.logger.info('[{}] Input arguments: {}'.format(chat_id, str_args))
        # TODO: chat_id, keywords DB 저장
        self.logger.info('[{}] Registered keywords: {}'.format(chat_id, str_args))
        update.message.reply_text('Registered keywords: {}'.format(str_args))

    def unregister_keywords(self, bot, update, args):
        chat_id = update.message.chat_id
        str_args = ' '.join(args)
        self.logger.info('[{}] Input arguments: {}'.format(chat_id, str_args))
        # TODO: keywords를 DB에서 제거
        self.logger.info('[{}] Unregistered keywords: {}'.format(chat_id, args))
        # TODO: 남은 keyword list DB에서 가져오기
        registered = []
        update.message.reply_text('Registered keywords: {}'.format(registered))

    def clear(self, bot, update):
        chat_id = update.message.chat_id
        # TODO: chat_id의 모든 keywords를 DB에서 제거
        self.logger.info('[{}] Unregistered all keywords'.format(chat_id))
        # TODO: 남은 keyword list DB에서 가져오기
        registered = []
        update.message.reply_text('Registered keywords: {}'.format(registered))

    def show_registered_keywords(self, bot, update):
        chat_id = update.message.chat_id
        # TODO: DB에서 chat_id로 등록된 keyword list 가져오기
        keywords = []
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
        # TODO: DB에서 사용자 제거
        self.logger.info('[{}] Bot unregistered.'.format(chat_id))

    def shutdown(self):
        self.updater.stop()
        self.updater.idle = False

    def run(self):
        self.updater.start_polling()
        self.logger.info('Start polling...')
