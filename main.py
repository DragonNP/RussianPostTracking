import telegram
import logging
import format_helper
import sys
from russian_post_tracking.soap import RussianPostTracking
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

login = sys.argv[1]
password = sys.argv[2]
bot_token = sys.argv[3]


def get_keyboard_track(barcode):
    keyboard = [
        [InlineKeyboardButton("Показать полный путь", callback_data='show_all_route_'+barcode)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_start_msg(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Этот бот может отслеживать посылки через сервис Почта России\n'
                              'Чтобы узнать где находится ваша посылка, просто введие номер отправления')


def send_track_wait(update: Update, context: CallbackContext) -> None:
    barcode = update.message.text

    message = update.message.reply_text('*Отслеживаю посылку..*', parse_mode=telegram.ParseMode.MARKDOWN)
    send_short_history(barcode, message)


def send_all_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('show_all_route_', '')
    tracking = RussianPostTracking(barcode, login, password)
    history_track = tracking.get_history()

    output = format_helper.format_route(history_track, barcode)
    query.edit_message_text(text=output, parse_mode=telegram.ParseMode.MARKDOWN)


def send_short_history(barcode, msg):
    tracking = RussianPostTracking(barcode, login, password)
    history_track = tracking.get_history()

    output = format_helper.format_route_short(history_track, barcode)

    msg.edit_text(output, reply_markup=get_keyboard_track(barcode), parse_mode=telegram.ParseMode.MARKDOWN)


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create the Updater and pass it your bot's token.
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', send_start_msg))
    dispatcher.add_handler(CommandHandler('help', send_start_msg))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_track_wait))
    dispatcher.add_handler(CallbackQueryHandler(send_all_history))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
