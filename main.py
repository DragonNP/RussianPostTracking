import telegram
import logging
import format_helper
import os
from russian_post_tracking.soap import RussianPostTracking
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

login = os.environ.get('RPT_LOGIN', None)
password = os.environ.get('RPT_PASSWORD', None)
bot_token = os.environ.get('TELEGRAM_API', None)

logger = logging.getLogger('main')


def get_keyboard_track(barcode):
    keyboard = [
        [InlineKeyboardButton("Показать полный путь", callback_data='show_all_route_'+barcode)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_start_msg(update: Update, context: CallbackContext) -> None:
    logger.info('Новое сообщение: /start или /help')

    update.message.reply_text('Этот бот может отслеживать посылки через сервис Почта России\n'
                              'Чтобы узнать где находится ваша посылка, просто введие номер отправления')


def send_track_wait(update: Update, context: CallbackContext) -> None:
    logger.info('Отправка истории передвижения посылки')
    barcode = update.message.text

    message = update.message.reply_text('*Отслеживаю посылку...*', parse_mode=telegram.ParseMode.MARKDOWN)
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
    if output is None:
        return msg.edit_text('*История передвежений посылки не найдена.*', parse_mode=telegram.ParseMode.MARKDOWN)

    msg.edit_text(output, reply_markup=get_keyboard_track(barcode), parse_mode=telegram.ParseMode.MARKDOWN)


def error_callback(update: Update, context: CallbackContext):
    error: Exception = context.error

    logger.error(error.__context__)
    update.message.reply_text('Введите корректный номер')


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
    dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    logger.info('Бот работает')
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
