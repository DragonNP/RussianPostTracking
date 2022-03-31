import datetime
import telegram
import logging
import format_helper
import os
from russian_post_tracking.soap import RussianPostTracking
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, \
    JobQueue

import refactor_track
from database import UsersDB, BarcodesDB
from package import Package

login = os.environ.get('RPT_LOGIN', None)
password = os.environ.get('RPT_PASSWORD', None)
bot_token = os.environ.get('TELEGRAM_API', None)
logger_level = os.environ.get('LOGGER_LEVEL', 'INFO')

logger = logging.getLogger('main')
logger.setLevel(logger_level)

users_db_path = './users.json'
barcodes_db_path = './barcodes.json'

users = UsersDB(users_db_path, logger_level)
barcodes_db = BarcodesDB(barcodes_db_path, logger_level)


def get_keyboard_track(barcode, is_tracked=False, is_show_all_track=True):
    keyboard = []

    if is_show_all_track:
        keyboard.append([InlineKeyboardButton("Показать полный путь", callback_data='show_all_route_' + barcode)])
    else:
        keyboard.append([InlineKeyboardButton("Показать последнее изменение", callback_data='show_short_route_' + barcode)])

    if is_tracked:
        keyboard.append([InlineKeyboardButton("Перестать отслеживать", callback_data='remove_from_tracked_' + barcode)])
    else:
        keyboard.append([InlineKeyboardButton("Отслеживать", callback_data=f'add_to_tracked_{barcode}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_start_msg(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    logger.info(f'Новое сообщение: /start или /help. пользователь:{user_id}')

    users.add_user(user_id)

    update.message.reply_text('Этот бот может отслеживать посылки через сервис Почта России\n'
                              'Чтобы узнать где находится ваша посылка, просто введие номер отправления')


def send_track_wait(update: Update, context: CallbackContext) -> None:
    barcode = update.message.text

    logger.info(f'Отправка истории передвижения посылки. пользователь:{update.effective_user.id}, трек-номер:{barcode}')

    message = update.message.reply_text('*Отслеживаю посылку...*', parse_mode=telegram.ParseMode.MARKDOWN)

    send_short_history(barcode=barcode, msg=message)


def route_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if 'show_all_route_' in query.data:
        return send_all_history(update, context)
    elif 'show_short_route_' in query.data:
        return edit_msg_send_short_history(update, context)
    elif 'add_to_tracked_' in query.data:
        return add_barcode_in_track(update, context)
    elif 'remove_from_tracked_' in query.data:
        return remove_barcode_in_track(update, context)


def send_all_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('show_all_route_', '')

    logger.info(f'Отправка полной информации о трек-номере. трек-номер:{barcode}, пользователь:{query.from_user.id}')

    package = Package(barcode, login, password, barcodes_db_path, logger_level)

    output = format_helper.format_route(package, barcode)

    isTracked = users.check_barcode(query.from_user.id, barcode)
    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_track(barcode, is_tracked=isTracked, is_show_all_track=False),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def add_barcode_in_track(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('add_to_tracked_', '')
    result = users.update_barcode(query.from_user.id, barcode)

    logger.info(f'Добавление трек-номера в отслеживаемое. трек-номер:{barcode}, пользователь:{query.from_user.id}')

    query.edit_message_reply_markup(reply_markup=get_keyboard_track(barcode, is_tracked=result))


def remove_barcode_in_track(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('remove_from_tracked_', '')
    result = not users.update_barcode(query.from_user.id, barcode, remove=True)

    logger.info(f'Удаление трек-номера в отслеживаемое. barcode:{barcode}, user:{query.from_user.id}')

    query.edit_message_reply_markup(reply_markup=get_keyboard_track(barcode, is_tracked=result))


def edit_msg_send_short_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('show_short_route_', '')

    logger.info(f'Отправка базовой информации о трек-номере. трек-номер:{barcode}, пользователь:{query.from_user.id}')

    package = Package(barcode, login, password, barcodes_db_path, logger_level)
    output = format_helper.format_route_short(package, barcode)

    is_tracked = users.check_barcode(query.from_user.id, barcode)
    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=False),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def send_short_history(barcode: str, user_id: int = 0, bot=None, msg: telegram.message.Message = None):
    logger.info(
        f'Отправка базовой информации о трек-номере. трек-номер:{barcode}, пользователь:{user_id if user_id > 0 else msg.chat_id}')

    package = Package(barcode, login, password, barcodes_db_path, logger_level)

    output = format_helper.format_route_short(package, barcode)

    if output is None:
        if user_id > 0:
            return bot.send_message(chat_id=user_id, text='*История передвежений посылки не найдена.*',
                                    parse_mode=telegram.ParseMode.MARKDOWN)
        return msg.edit_text('*История передвежений посылки не найдена.*', parse_mode=telegram.ParseMode.MARKDOWN)

    if user_id > 0:
        is_tracked = users.check_barcode(user_id, barcode)
        return bot.send_message(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN,
                                reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked))
    is_tracked = users.check_barcode(msg.chat_id, barcode)
    return msg.edit_text(output, reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked),
                         parse_mode=telegram.ParseMode.MARKDOWN)


def check_new_update(context: CallbackContext):
    database = users.get_db()

    for user_id in database:
        barcodes = database[user_id]['barcodes']

        for curr_barcode in barcodes:
            tracking = RussianPostTracking(curr_barcode, login, password)
            history_track = refactor_track.convert_to_json(tracking.get_history())

            if history_track == barcodes_db.get_history_track(curr_barcode):
                continue

            barcodes_db.update_history_track(curr_barcode, history_track)
            send_short_history(barcode=curr_barcode, user_id=int(user_id), bot=context.bot)


def error_callback(update: Update, context: CallbackContext):
    error: Exception = context.error

    logger.error(error)
    update.message.reply_text('Введите корректный номер')


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create the Updater and pass it your bot token.
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', send_start_msg))
    dispatcher.add_handler(CommandHandler('help', send_start_msg))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_track_wait))
    dispatcher.add_handler(CallbackQueryHandler(route_callback))
    dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    # j: JobQueue = updater.job_queue
    # j.run_daily(check_new_update, days=(0, 1, 2, 3, 4, 5, 6),
    #             time=datetime.time(hour=10 - 3, minute=00, second=00))
    #
    # j.run_once(check_new_update, 30)

    logger.info('Бот работает')
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
