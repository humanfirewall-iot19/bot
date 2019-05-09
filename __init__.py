import logging
import os
from io import BytesIO

import requests
from PIL import Image

from pyzbar.pyzbar import decode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

from .bot_helper import get_url, build_menu
from .db_helper import DBHelper

REQUEST_NAME_CONFIGURE = 2
CONFIGURE_RESPONSE = 1


class Bot:
    updater = None

    def __init__(self, token):
        self.updater = Updater(token)
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('test', self._test_notification))
        dp.add_handler(CommandHandler('help', help))
        dp.add_handler(ConversationHandler(
            entry_points=[CommandHandler('configure', _configure_start)],
            states={
                REQUEST_NAME_CONFIGURE: [MessageHandler(Filters.text, request_name, pass_user_data=True)],
                CONFIGURE_RESPONSE: [
                    MessageHandler((Filters.text | Filters.photo), self.received_deviceid, pass_user_data=True)]
            },
            fallbacks=[CommandHandler('cancel', _cancel)]))
        dp.add_handler(CallbackQueryHandler(self._handle_callback_feedback))

    def send_message(self, chat_id, message):
        self.updater.bot.send_message(text=message, chat_id=chat_id)

    def send_notification(self, board_id, target_id, url_photo):
        db = DBHelper()
        db.connect()
        chat_ids = db.get_chatID_by_device(str(board_id))
        feedback = db.get_feedback_by_target(target_id)
        for chat_id in chat_ids:
            if url_photo is None:
                url_photo = get_url()
            button_list = [
                InlineKeyboardButton("Lascia un feedback", callback_data="Feedback,{}".format(target_id)),
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            self.updater.bot.send_photo(chat_id=chat_id, photo=url_photo, timeout=30)
            text = "Pensiamo che utente {} abbia suonato alla porta!".format(target_id)

            if feedback is None:
                text += "\nPersona ignota."
            elif feedback[0] > feedback[1]:
                text += "\nE' uno scammer conosciuto."
            elif feedback[1] > feedback[0]:
                text += "\nNon è classificato come scammer."
            else:
                text += "\nNon siamo certi sulla valutazione della persona."
            self.updater.bot.send_message(chat_id=chat_id,
                                          text=text,
                                          reply_markup=reply_markup)
        db.close()

    def start(self):
        self.updater.start_polling()
        # self.updater.idle()

    def stop(self):
        self.updater.stop()

    def _handle_callback_feedback(self, bot, update):
        data = str(update.callback_query.data)
        target = data.split(",")[1]
        if data.startswith("Feedback"):
            button_list = [
                InlineKeyboardButton("Scammer", callback_data="Scammer,{}".format(target)),
                InlineKeyboardButton("Not-scammer", callback_data="Not-Scammer,{}".format(target))
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            update.callback_query.edit_message_text(
                text="Che feedback ci vorresti lasciare?".format(
                    data.split(",")[1]),
                reply_markup=reply_markup
            )
        else:
            feedback = data.split(",")[0]
            target = data.split(",")[1]
            unwanted = 0
            if feedback == "Scammer":
                unwanted = 1
            db = DBHelper()
            db.connect()
            db.add_feedback(str(update.callback_query.message.chat.id), target, unwanted)
            db.close()
            update.callback_query.edit_message_text(
                text="Grazie per il feedback!",
            )

    def received_deviceid(self, bot, update, user_data):
        chat_id = str(update.message.chat_id)
        if update.message.text is None and (update.message.photo is None or len(update.message.photo) == 0):
            bot.send_message(chat_id=chat_id, text="Devi scrivere l'id o mandare una foto con un QRCODE!")
            return
        if update.message.photo is not None and len(update.message.photo) > 0:
            photo_id = update.message.photo[-1].file_id
            img_file = bot.get_file(photo_id)
            response = requests.get(img_file.file_path)
            raw_img = BytesIO(response.content)
            img = Image.open(raw_img)
            intercom_id = list(filter(lambda x: x.type == "QRCODE", decode(img)))[0].data.strip()
        else:
            intercom_id = str(update.message.text).strip()

        bot.send_message(chat_id=chat_id, text="Ho correttamente configura l'id {}".format(intercom_id))
        db = DBHelper()
        db.connect()
        db.add_user(str(intercom_id), str(chat_id))
        db.close()
        return ConversationHandler.END

    def _test_notification(self, bot, update):
        self.send_notification("1", "1", None)


def _help(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Benvenuto nel bot del progetto Human Firewall \n che ti aiuterá ad identificare le persone "
                          "alla porta")


def _configure_start(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Inserisci il nome del citofono per iniziare a ricevere le notifiche di chi ti suona alla "
                          "porta")
    return REQUEST_NAME_CONFIGURE


def request_name(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    update.message.reply_text(
        'Ok what is the id for {}?'.format(text.lower()))
    return CONFIGURE_RESPONSE


def _cancel(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Operazione annullata.\nRicordati che devi avere almeno un "
                                                          "dispositivo configurato per utilizzare questo bot al meglio!")
    return ConversationHandler.END
