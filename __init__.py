import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

from .bot_helper import get_url, build_menu
from .db_helper import DBHelper

CONFIGURE_RESPONSE = 1


class Bot:
    updater = None

    def __init__(self):
        self.updater = Updater('893974066:AAHS53j4hGLEn-5RB6GLhinDY2IUpPaar3w')
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('test', self._test_notification))
        dp.add_handler(CommandHandler('help', help))
        dp.add_handler(ConversationHandler(
            entry_points=[CommandHandler('configure', _configure_start)],
            states={
                CONFIGURE_RESPONSE: [MessageHandler(Filters.text, self.received_deviceid)]
            },
            fallbacks=[CommandHandler('cancel', _cancel)]))
        dp.add_handler(CallbackQueryHandler(self._handle_callback_feedback))

    def send_message(self, chat_id, message):
        self.updater.bot.send_message(text=message, chat_id=chat_id)

    def send_notification(self, board_id, target_id, url_photo):
        db = DBHelper()
        db.connect()
        chat_ids = db.get_chatID_by_device(str(board_id))
        db.close()
        for chat_id in chat_ids:
            url = get_url()
            button_list = [
                InlineKeyboardButton("Lascia un feedback", callback_data="Feedback,{}".format(target_id)),
            ]
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            self.updater.bot.send_photo(chat_id=chat_id, photo=url)
            self.updater.bot.send_message(chat_id=chat_id,
                                        text="Pensiamo che utente {} abbia suonato alla porta!".format(target_id),
                                        reply_markup=reply_markup)

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

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

    def received_deviceid(self, bot, update):
        chat_id = str(update.message.chat_id)
        msg = str(update.message.text).strip()
        bot.send_message(chat_id=chat_id, text="Ho correttamente configura l'id {}".format(msg))
        db = DBHelper()
        db.connect()
        db.add_user(str(msg), str(chat_id))
        db.close()
        return ConversationHandler.END

    def _test_notification(self, bot, update):
        self.send_notification(1, 1, None)


def _help(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Benvenuto nel bot del progetto Human Firewall \n che ti aiuterá ad identificare le persone "
                          "alla porta")


def _configure_start(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,
                     text="Inserisci il codice del citofono per iniziare a ricevere le notifiche di chi ti suona alla "
                          "porta")
    return CONFIGURE_RESPONSE


def _cancel(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Operazione annullata.\nRicordati che devi avere almeno un "
                                                          "dispositivo configurato per utilizzare questo bot al meglio!")
    return ConversationHandler.END


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    pussa_via = Bot()
    pussa_via.start()
