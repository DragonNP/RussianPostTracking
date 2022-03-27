import telegram
import logging
import format_helper
import os
from russian_post_tracking.soap import RussianPostTracking
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from database import UsersDB

login = os.environ.get('RPT_LOGIN', None)
password = os.environ.get('RPT_PASSWORD', None)
bot_token = os.environ.get('TELEGRAM_API', None)

logger = logging.getLogger('main')

users = UsersDB('./users.json')


def get_keyboard_track(barcode, isTracked=False):
    keyboard = [
        [InlineKeyboardButton("Показать полный путь", callback_data='show_all_route_' + barcode)],
    ]

    if isTracked:
        keyboard.append([InlineKeyboardButton("Перестать отслеживать", callback_data='remove_from_tracked' + barcode)])
    else:
        keyboard.append([InlineKeyboardButton("Отслеживать", callback_data='add_to_tracked_' + barcode)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_start_msg(update: Update, context: CallbackContext) -> None:
    logger.info('Новое сообщение: /start или /help')

    users.add_user(update.message.from_user.id)

    update.message.reply_text('Этот бот может отслеживать посылки через сервис Почта России\n'
                              'Чтобы узнать где находится ваша посылка, просто введие номер отправления')


def send_track_wait(update: Update, context: CallbackContext) -> None:
    logger.info('Отправка истории передвижения посылки')
    barcode = update.message.text

    message = update.message.reply_text('*Отслеживаю посылку...*', parse_mode=telegram.ParseMode.MARKDOWN)
    send_short_history(barcode, message)


def route_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if 'show_all_route_' in query.data:
        return send_all_history(update, context)
    elif 'add_to_tracked_' in query.data:
        return add_barcode_in_track(update, context)
    elif 'remove_from_tracked' in query.data:
        return remove_barcode_in_track(update, context)


def send_all_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('show_all_route_', '')
    tracking = RussianPostTracking(barcode, login, password)
    history_track = tracking.get_history()

    logger.info(f'Отправка полной информации о трек-номере. barcode:{barcode}, user:{query.from_user.id}')

    output = format_helper.format_route(history_track, barcode)
    isTracked = users.check_barcode(query.from_user.id, barcode)
    query.edit_message_text(text=output, reply_markup=get_keyboard_track(barcode, isTracked=isTracked),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def add_barcode_in_track(update: Update, context: CallbackContext) -> None:

    query = update.callback_query
    query.answer()

    barcode = query.data.replace('add_to_tracked_', '')
    result = users.update_barcode(query.from_user.id, barcode)

    logger.info(f'Добавление трек-номера в отслеживаемое. barcode:{barcode}, user:{query.from_user.id}')

    query.edit_message_reply_markup(reply_markup=get_keyboard_track(barcode, isTracked=result))


def remove_barcode_in_track(update: Update, context: CallbackContext) -> None:

    query = update.callback_query
    query.answer()

    barcode = query.data.replace('remove_from_tracked', '')
    result = not users.update_barcode(query.from_user.id, barcode, remove=True)

    logger.info(f'Удаление трек-номера в отслеживаемое. barcode:{barcode}, user:{query.from_user.id}')

    query.edit_message_reply_markup(reply_markup=get_keyboard_track(barcode, isTracked=result))


def send_short_history(barcode, msg):
    logger.info(f'Отправка базовой информации о трек-номере. barcode:{barcode}, user:{msg.chat_id}')

    tracking = RussianPostTracking(barcode, login, password)
    history_track = tracking.get_history()

    output = format_helper.format_route_short(history_track, barcode)

    if output is None:
        return msg.edit_text('*История передвежений посылки не найдена.*', parse_mode=telegram.ParseMode.MARKDOWN)

    isTracked = users.check_barcode(msg.chat_id, barcode)
    msg.edit_text(output, reply_markup=get_keyboard_track(barcode, isTracked=isTracked),
                  parse_mode=telegram.ParseMode.MARKDOWN)


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
    dispatcher.add_handler(CallbackQueryHandler(route_callback))
    dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    logger.info('Бот работает')
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
