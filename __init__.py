from io import BytesIO

import requests
import telegram
from PIL import Image
from pyzbar.pyzbar import decode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

from .bot_helper import get_url, build_menu
from .db_helper import DBHelper

DEVICE_NAME_GET = 2
DEVICE_ID_GET = 1
HANDLER_DELETE = 3


class Bot:
    updater = None

    def __init__(self, token):
        self.updater = Updater(token)
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
                DEVICE_NAME_GET: [MessageHandler(Filters.text, request_name, pass_user_data=True)],
                DEVICE_ID_GET: [
                    MessageHandler((Filters.text | Filters.photo), self.received_deviceid, pass_user_data=True)]
            },
            fallbacks=[CommandHandler('cancel', _cancel)]))
        dp.add_handler(CallbackQueryHandler(self._handle_callback_feedback))

    def send_message(self, chat_id, message):
        self.updater.bot.send_message(text=message, chat_id=chat_id)

    def send_notification(self, board_id, target_id, photo, has_face=True):
        db = DBHelper()
        db.connect()
        chat_ids = db.get_chatID_by_device(str(board_id))
        feedback = db.get_feedback_by_target(target_id)
        for chat_id in chat_ids:
            device_name = db.get_device_name_by_chatID_and_device(chat_id, board_id)
            try:
                self.updater.bot.send_photo(chat_id=chat_id, photo=photo, timeout=120)
            except telegram.error.TimedOut:
                pass
            if hasattr(photo, "seek"):
                photo.seek(0)
            if has_face:
                button_list = [
                    InlineKeyboardButton("Leave a feedback", callback_data="feedback,{}".format(target_id)),
                ]
                reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
                text = "[{}] We think that the subject {} has rang the doorbell!".format(device_name, target_id)
                if feedback is None:
                    text += "\nUnknown identity."
                elif feedback[0] > feedback[1]:
                    text += "\nIt's an unwanted guest."
                elif feedback[1] > feedback[0]:
                    text += "\nIt isn't classified as an unwanted guest."
                else:
                    text += "\nWe are not sure about the user evaluation."
                self.updater.bot.send_message(chat_id=chat_id,
                                              text=text,
                                              reply_markup=reply_markup)
            else:
                text = "[{}] Someone rang the doorbell but we don't know who did it.".format(device_name)
                self.updater.bot.send_message(chat_id=chat_id, text=text)
        db.close()

    def start(self):
        self.updater.start_polling()
        # self.updater.idle()

    def stop(self):
        self.updater.stop()

    def _handle_callback_feedback(self, bot, update):
        data = str(update.callback_query.data)
        if not data.startswith("feedback") and not data.startswith("result_feedback"):
            pass
        target = data.split(",")[1]
        if data.startswith("feedback"):
            button_list = [
                InlineKeyboardButton("Scammer", callback_data="result_feedback,Scammer,{}".format(target)),
                InlineKeyboardButton("Not-scammer", callback_data="result_feedback,Not-Scammer,{}".format(target))
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            update.callback_query.edit_message_text(
                text="Which feedback you would like to give?".format(
                    data.split(",")[1]),
                reply_markup=reply_markup
            )
        else:
            feedback = data.split(",")[1]
            target = data.split(",")[2]
            unwanted = 0
            if feedback == "Scammer":
                unwanted = 1
            db = DBHelper()
            db.connect()
            db.add_feedback(str(update.callback_query.message.chat.id), target, unwanted)
            db.close()
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
        db = DBHelper()
        db.connect()
        db.add_user(str(intercom_id), str(device_name), str(chat_id))
        db.close()
        return ConversationHandler.END

    def _test_notification(self, bot, update):
        self.send_notification("1", "1", get_url(), has_face=True)

    def delete(self, bot, update):
        chat_id = str(update.message.chat_id)
        db = DBHelper()
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
        db = DBHelper()
        db.connect()
        db.delete_user_by_id_and_device_name(device_name, str(update.callback_query.message.chat.id))
        update.callback_query.edit_message_text(
            text="Device successfully removed")
        return ConversationHandler.END


def _help(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Welcome to the bot of the Human Firewall project. \nIt will help you to identify unwanted guest at your doorstep ")


def _configure_start(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Insert the name of the intercom that you would like to configure.")
    return DEVICE_NAME_GET


def request_name(bot, update, user_data):
    text = update.message.text
    user_data['device_name'] = text
    db = DBHelper()
    db.connect()

    names = db.get_device_names_by_chatID(str(update.message.chat_id))
    if text in names:
        update.message.reply_text(
            'Device name must be unique!\nTry again'.format(text))
        return DEVICE_NAME_GET
    update.message.reply_text(
        'Ok what is the id for {}?'.format(text))
    return DEVICE_ID_GET


def _cancel(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Operazione annullata.\nRicordati che devi avere almeno un "
                                                          "dispositivo configurato per utilizzare questo bot al meglio!")
    return ConversationHandler.END
