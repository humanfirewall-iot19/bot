from threading import Lock

import requests
import telegram
import sys
import logging
from PIL import Image
from pyzbar.pyzbar import decode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

from .board_db_helper import BoardDBHelper
from .bot_helper import get_url, build_menu
from .queue_publisher import *

DEVICE_NAME_GET = 2
DEVICE_ID_GET = 1
HANDLER_DELETE = 3
LIST_LENGTH = 1500


class Bot:

    def __init__(self, token, ip_broker, db_path=None, debug = False):
        if debug: 
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)
        self.lock = Lock()
        self._load(token, db_path, ip_broker)

    def _load(self, token, db_path, ip_broker):
        self.start_time = int(time.time())
        self.token = token
        self.ip_broker = ip_broker
        self.updater = Updater(token)
        self.db_path = db_path
        self.mqtt = QueuePublisher(ip_broker)
        self.list_requests = [None] * LIST_LENGTH
        self.list_index = 0
        dp = self.updater.dispatcher
        dp.add_handler(ConversationHandler(
            entry_points=[CommandHandler('delete', self.delete)],
            states={
                HANDLER_DELETE: [CallbackQueryHandler(self._handle_callback_delete)],
            }, fallbacks=[CommandHandler('cancel', _cancel)]))
        dp.add_handler(CommandHandler('test', self._test_notification))
        dp.add_handler(CommandHandler('help', help))
        dp.add_handler(ConversationHandler(
            entry_points=[CommandHandler('configure', _configure_start)],
            states={
                DEVICE_NAME_GET: [MessageHandler(Filters.text, self.request_name, pass_user_data=True)],
                DEVICE_ID_GET: [
                    MessageHandler((Filters.text | Filters.photo), self.received_deviceid, pass_user_data=True)]
            },
            fallbacks=[CommandHandler('cancel', _cancel)]))
        dp.add_handler(CallbackQueryHandler(self._handle_callback_feedback))

    def reload(self):
        self.lock.acquire()
        try:
            self.updater.stop()
            self.mqtt.stop()
            self._load(self.token, self.db_path, self.ip_broker)
            self.start()
        finally:
            self.lock.release()

    def send_message(self, chat_id, message):
        self.updater.bot.send_message(text=message, chat_id=chat_id, )

    def send_notification(self, board_id, encoding, feedback, photo, has_face):
        self.lock.acquire()
        try:
            db = BoardDBHelper(abs_path=self.db_path)
            db.connect()
            chat_ids = db.get_chatID_by_device(str(board_id))
            for chat_id in chat_ids:
                device_name = db.get_device_name_by_chatID_and_device(chat_id, board_id)
                feedback_message = None
                try:
                    self.updater.bot.send_photo(chat_id=chat_id, photo=photo, timeout=120)
                except telegram.error.TimedOut:
                    pass
                if hasattr(photo, "seek"):
                    photo.seek(0)
                if has_face:
                    button_list = [
                        InlineKeyboardButton("Leave a feedback",
                                             callback_data="feedback@{}@{}".format(self.list_index, self.start_time)),
                    ]
                    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
                    text = "[{}] Someone has rang the doorbell!".format(device_name)
                    if feedback is None:
                        text += "\nNo feedback is avaiable."
                    elif feedback[0] > feedback[1]:
                        text += "\nIt's an unwanted guest. \u26a0"
                    elif feedback[1] > feedback[0]:
                        text += "\nIt is a trusted guest. \u2705"
                    else:
                        text += "\nWe are not sure about the user evaluation."
                    feedback_message = self.updater.bot.send_message(chat_id=chat_id,
                                                                     text=text,
                                                                     reply_markup=reply_markup)
                else:
                    text = "[{}] Someone rang the doorbell but we don't know who did it.".format(device_name)
                    feedback_message = self.updater.bot.send_message(chat_id=chat_id, text=text)

                if feedback_message is not None:
                    self.add_to_feedback_list((feedback_message, encoding, self.start_time))
            db.close()
        finally:
            self.lock.release()

    def add_to_feedback_list(self, element):
        old_elem = self.list_requests[self.list_index]
        if old_elem is not None:
            try:
                old_msg = old_elem[0]
                self.updater.bot.edit_message_text(chat_id=old_msg.chat.id, message_id=old_msg.message_id, text= old_msg.text)
            except Exception as e:
                print(e)

        self.list_requests[self.list_index] = element
        print(sys.getsizeof(element))
        self.list_index += 1
        if self.list_index == LIST_LENGTH:
            self.list_index = 0

    def start(self):
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()

    def _handle_callback_feedback(self, bot, update):
        data = str(update.callback_query.data)
        if not data.startswith("feedback") and not data.startswith("result_feedback"):
            pass
        if data.startswith("feedback"):
            list_index = data.split("@")[1]
            bot_start_time = data.split("@")[2]
            button_list = [
                InlineKeyboardButton("Scammer",
                                     callback_data="result_feedback@Scammer@{}@{}".format(list_index, bot_start_time)),
                InlineKeyboardButton("Not-scammer",
                                     callback_data="result_feedback@Not-Scammer@{}@{}".format(list_index, bot_start_time))
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            update.callback_query.edit_message_text(
                text="Which feedback you would like to give?".format(
                    data.split("@")[1]),
                reply_markup=reply_markup
            )
        else:
            feedback = data.split("@")[1]
            list_index = int(data.split("@")[2])
            bot_start_time = int(data.split("@")[3])
            unwanted = 0
            if feedback == "Scammer":
                unwanted = 1
            self.lock.acquire()
            try:
                if bot_start_time == self.start_time:
                    list_elem = self.list_requests[list_index]
                    if list_elem is not None and int(list_elem[2]) == self.start_time and list_elem[0].chat.id == update.callback_query.message.chat.id:
                        self.mqtt.publishResults(list_elem[1], unwanted,
                                                 str(update.callback_query.message.chat.id), time.time())
            finally:
                self.lock.release()
            update.callback_query.edit_message_text(
                text="Thank you for the feedback!",
            )

    def received_deviceid(self, bot, update, user_data):
        chat_id = str(update.message.chat_id)
        device_name = user_data["device_name"]
        if device_name is None:
            bot.send_message(chat_id=chat_id, text="An unexpected error happened!\nTry again later")
            pass
        if update.message.text is None and (update.message.photo is None or len(update.message.photo) == 0):
            bot.send_message(chat_id=chat_id, text="You have to write a valid id or send a QRCODE as a photo!")
            return
        if update.message.photo is not None and len(update.message.photo) > 0:
            photo_id = update.message.photo[-1].file_id
            img_file = bot.get_file(photo_id)
            response = requests.get(img_file.file_path)
            raw_img = BytesIO(response.content)
            img = Image.open(raw_img)
            intercom_id = str(list(filter(lambda x: x.type == "QRCODE", decode(img)))[0].data).split("'")[1]
        else:
            intercom_id = str(update.message.text).strip()

        bot.send_message(chat_id=chat_id, text="You correctly configured the intercom with id {}.\nYou will now be "
                                               "able to receive the notifications from that intercom!".format(
            intercom_id))
        db = BoardDBHelper(abs_path=self.db_path)
        db.connect()
        db.add_user(str(intercom_id), str(device_name), str(chat_id))
        db.close()
        return ConversationHandler.END

    def _test_notification(self, bot, update):
        self.send_notification("1", "333", [1, 0], get_url(), True)

    def delete(self, bot, update):
        chat_id = str(update.message.chat_id)
        db = BoardDBHelper(abs_path=self.db_path)
        db.connect()
        device_names = db.get_device_names_by_chatID(chat_id)
        buttons_list = []
        for device in device_names:
            buttons_list.append(InlineKeyboardButton(device, callback_data=device))
        reply_markup = InlineKeyboardMarkup(build_menu(buttons_list, n_cols=1))
        if len(buttons_list) == 0:
            update.message.reply_text('No device added were found!')
            return ConversationHandler.END
        else:
            update.message.reply_text('What intercom do you want to remove?', reply_markup=reply_markup)
        db.close()
        return HANDLER_DELETE

    def _handle_callback_delete(self, bot, update):
        device_name = str(update.callback_query.data)
        db = BoardDBHelper(abs_path=self.db_path)
        db.connect()
        db.delete_user_by_id_and_device_name(device_name, str(update.callback_query.message.chat.id))
        update.callback_query.edit_message_text(
            text="Device successfully removed")
        return ConversationHandler.END

    def request_name(self, bot, update, user_data):
        text = update.message.text
        user_data['device_name'] = text
        db = BoardDBHelper(abs_path=self.db_path)
        db.connect()

        names = db.get_device_names_by_chatID(str(update.message.chat_id))
        if text in names:
            update.message.reply_text(
                'Device name must be unique!\nTry again'.format(text))
            return DEVICE_NAME_GET
        update.message.reply_text(
            'Ok what is the id for {}?'.format(text))
        return DEVICE_ID_GET


def _help(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Welcome to the bot of the Human Firewall project. \nIt will help you to identify unwanted guest at your doorstep ")


def _configure_start(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Insert the name of the intercom that you would like to configure.")
    return DEVICE_NAME_GET


def _cancel(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Operazione annullata.\nRicordati che devi avere almeno un "
                                                          "dispositivo configurato per utilizzare questo bot al meglio!")
    return ConversationHandler.END
