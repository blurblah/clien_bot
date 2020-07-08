
import json
import logging
import time
from functools import wraps

import pika
import telegram
from telegram.error import Unauthorized, TimedOut, NetworkError
from telegram.ext import Updater, CommandHandler

from bot.data_service import DataService
from bot.env import Environments


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

    def __init__(self, token, mongo_uri):
        self.logger = logging.getLogger('bot')
        self.__bot = telegram.Bot(token=token)
        self.updater = Updater(bot=self.__bot)
        self.dispatcher = self.updater.dispatcher
        self.init_handlers()
        self.data_service = DataService(mongo_uri)
        # 게시판 종류는 우선 하나만
        self.board = 'allsell'
        self.keyboard = [
            ['/register', '/list'],
            ['/clear', '/help']
        ]
        self.env = Environments()
        self._connection = None
        self._channel = None
        self._stopping = False
        self._consumer_tag = None

    def connect(self, mq_host, mq_port):
        self.logger.info('Connecting to {}:{}...'.format(mq_host, mq_port))
        conn = pika.SelectConnection(
            pika.ConnectionParameters(host=mq_host, port=mq_port),
            on_open_callback=self.on_connection_open,
            on_close_callback=self.on_connection_closed
        )
        conn.add_on_open_error_callback(self.on_connection_open_error)
        return conn

    def reconnect(self):
        delay = 30
        self._connection.ioloop.stop()
        time.sleep(delay)
        self.logger.info('Try to reconnect after {} seconds'.format(delay))
        if not self._stopping:
            self._connection = self.connect(self.env.config['MQ_HOST'], self.env.config['MQ_PORT'])
            self._connection.ioloop.start()

    def on_connection_closed(self, _unused_connection, reason):
        self._channel = None
        if self._stopping:
            self.logger.info('Stopping...')
            self._connection.ioloop.stop()
        else:
            self.logger.warning('Connection closed, reconnect necessary: {}'.format(reason))
            self.reconnect()

    def on_connection_open(self, _unused_connection):
        self.logger.info('Connected.')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        self.logger.error('Connection open error: {}'.format(err))
        self.reconnect()

    def open_channel(self):
        self.logger.info('Creating a new channel...')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self.logger.info('Channel opened.')
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self.setup_queue(self.board)

    def setup_queue(self, queue):
        self._channel.queue_declare(queue=queue)
        self._channel.basic_qos(prefetch_count=1)
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self._consumer_tag = self._channel.basic_consume(queue=queue, on_message_callback=self.consumer_cb)

    def on_consumer_cancelled(self, method_frame):
        self.logger.info('Consumer was cancelled. Shutting down: {}'.format(method_frame))
        if self._channel:
            self._channel.close()

    def on_channel_closed(self, channel, reason):
        self.logger.warning('Channel {} was closed: {}'.format(channel, reason))
        self._channel = None
        self._connection.close()

    def stop_consuming(self):
        if self._channel:
            self.logger.info('Sending a Basic.Cancel RPC command to RabbitMQ...')
            self._channel.basic_cancel(self._consumer_tag, self.on_cancel_ok)

    def on_cancel_ok(self, unused_frame):
        self.logger.info('Cancel OK.')
        self.logger.info('Closing channel...')
        self._channel.close()

    def consumer_cb(self, ch, method, properties, body):
        received = json.loads(body)
        chat_id = received['chat_id'] if 'chat_id' in received else None
        message = received['message'] if 'message' in received else None
        if not chat_id or not message:
            self.logger.warning('chat_id or message is None. received: {}'.format(received))
            return

        message = message.strip()
        self.logger.info('Received body chat_id: {}  message: {}'.
                         format(received['chat_id'], received['message']))
        try:
            self.send_message(chat_id, message, telegram.ParseMode.MARKDOWN)
        except Unauthorized as e:
            self.logger.warning('[{}] Unauthoriezed exception. Details: {}'
                                .format(chat_id, str(e)))
        except TimedOut as e:
            self.logger.warning('[{}] Timed out exception. Details: {}'
                                .format(chat_id, str(e)))
        except NetworkError as e:
            self.logger.warning('[{}] Network error exception. Details: {}'
                                .format(chat_id, str(e)))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def init_handlers(self):
        self.add_handler('start', self.start_bot)
        self.add_handler('register', self.register_keywords, has_args=True)
        self.add_handler('list', self.show_registered_keywords)
        self.add_handler('stop', self.stop_bot)
        self.add_handler('clear', self.clear)
        self.add_handler('help', self.help)

    def add_handler(self, command, callback, has_args=False):
        handler = CommandHandler(command, callback, pass_args=has_args)
        self.dispatcher.add_handler(handler)
        self.logger.info('Registered handler for command {}.'.format(command))

    @Decorators.send_typing_action
    def start_bot(self, bot, update):
        chat_id = update.message.chat_id
        # chat_id DB 저장
        inserted = self.data_service.insert_new_chat_id(chat_id)
        self.logger.info('[{}] Bot registered. inserted_id: {}'.format(chat_id, inserted))
        welcome_lines = [
            '클리앙 알리미 봇입니다.',
            '현재는 사고팔고 게시판에 대해서만 서비스가 가능합니다.'
        ]
        update.message.reply_text('\n'.join(welcome_lines))
        # reply_markup = telegram.ReplyKeyboardMarkup(self.keyboard)
        # self.send_message(chat_id, self._make_help_message(), telegram.ParseMode.MARKDOWN, reply_markup)
        self.send_message(chat_id, self._make_help_message(), telegram.ParseMode.MARKDOWN)

    @Decorators.send_typing_action
    def register_keywords(self, bot, update, args):
        chat_id = update.message.chat_id
        if len(args) < 1:
            update.message.reply_text('키워드가 입력되지 않았습니다.')
        else:
            str_args = ','.join(args)
            self.logger.info('[{}] Input arguments: {}'.format(chat_id, str_args))
            # chat_id, keywords DB 저장
            updated = self.data_service.update_keywords(chat_id, self.board, args)
            self.logger.info('[{}] Updated id: {}'.format(chat_id, updated))
            self.logger.info('[{}] Registered keywords: {}'.format(chat_id, str_args))
            messages = [
                '키워드가 등록되었습니다.',
                '등록된 키워드: _{}_'.format(str_args)
            ]
            update.message.reply_text('\n'.join(messages), parse_mode=telegram.ParseMode.MARKDOWN)

    @Decorators.send_typing_action
    def clear(self, bot, update):
        chat_id = update.message.chat_id
        # chat_id의 모든 keywords를 DB에서 제거
        updated = self.data_service.clear_keywords(chat_id, self.board)
        self.logger.info('[{}] Updated id: {}'.format(chat_id, updated))
        self.logger.info('[{}] Unregistered all keywords'.format(chat_id))
        # keyword list DB에서 가져오기
        # registered = self.data_service.select_keywords(chat_id, self.board)
        update.message.reply_text('키워드 리스트가 초기화 되었습니다.')

    @Decorators.send_typing_action
    def show_registered_keywords(self, bot, update):
        chat_id = update.message.chat_id
        # DB에서 chat_id로 등록된 keyword list 가져오기
        keywords = self.data_service.select_keywords(chat_id, self.board)
        self.logger.info('[{}] Registered keywords: {}'.format(chat_id, keywords))
        if len(keywords) > 0:
            msg = '현재 등록되어있는 키워드: _{}_'.format(','.join(keywords))
        else:
            msg = '등록된 키워드가 없습니다.'
        update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)

    @Decorators.send_typing_action
    def help(self, bot, update):
        chat_id = update.message.chat_id
        self.logger.info('[{}] Help message requested.'.format(chat_id))
        update.message.reply_text(self._make_help_message(), parse_mode=telegram.ParseMode.MARKDOWN)

    def send_message(self, chat_id, msg, parse_mode=None, reply_markup=None):
        self.__bot.send_message(chat_id=chat_id, text=msg, parse_mode=parse_mode, reply_markup=reply_markup)
        self.logger.info('[{}] Sent message: {}'.format(chat_id, msg))

    def stop_bot(self, bot, update):
        chat_id = update.message.chat_id
        # DB에서 사용자 제거
        self.data_service.delete_chat_id(chat_id)
        self.logger.info('[{}] Bot unregistered.'.format(chat_id))

    def stop(self):
        self._stopping = True
        self.logger.info('Stop consuming...')
        self.stop_consuming()
        self._connection.ioloop.start()
        self.updater.stop()
        self.updater.idle = False

    def run(self):
        self.updater.start_polling()
        self.logger.info('Start polling...')
        while not self._stopping:
            self._connection = None
            try:
                self._connection = self.connect(self.env.config['MQ_HOST'], self.env.config['MQ_PORT'])
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()
        self.logger.info('Stopped.')

    def _make_help_message(self):
        help_lines = [
            '<클리앙 알리미 도움말>',
            '*/start* : 시작',
            '*/register* : 키워드 등록',
            '  _/register 키워드1 키워드2 키워드3&키워드4..._',
            '  _참고1 : 키워드 여러개를 &와 붙여서 지정시 여러개 키워드가 동시에 존재하는 게시물을 찾습니다._',
            '  _참고2 : 이미 등록한 키워드 리스트가 있다면 일괄 교체합니다._',
            '*/list* : 등록한 키워드 리스트 표시',
            '*/clear* : 등록 키워드 전체 삭제',
            '*/help* : 도움말 표시',
            '문의사항이 있다면 *blurblah@blurblah.net*으로 연락주세요.'
        ]
        return '\n'.join(help_lines)
