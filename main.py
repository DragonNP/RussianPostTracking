from const_variables import *
import telegram
import datetime
import logging
import format_helper
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, \
    JobQueue
from package import Package

logger = logging.getLogger('main')
logger.setLevel(GLOBAL_LOGGER_LEVEL)

users = USERS_DATABASE
barcodes_db = BARCODES_DATABASE


def get_keyboard_track(barcode, is_tracked=False, is_show_all_track=True):
    keyboard = []

    if is_show_all_track:
        keyboard.append([InlineKeyboardButton("Показать полный путь", callback_data='show_all_route_' + barcode)])
    else:
        keyboard.append(
            [InlineKeyboardButton("Показать последнее изменение", callback_data='show_short_route_' + barcode)])

    if is_tracked:
        keyboard.append([InlineKeyboardButton("Перестать отслеживать",
                                              callback_data=f'remove_from_tracked_{barcode}_{int(is_show_all_track)}')])
    else:
        keyboard.append(
            [InlineKeyboardButton("Отслеживать", callback_data=f'add_to_tracked_{barcode}_{int(is_show_all_track)}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_keyboard_my_packages():
    keyboard = [['Показать отслеживаемое']]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return reply_markup


def get_keyboard_remove_delivered():
    keyboard = [[InlineKeyboardButton('Удалить доставленные', callback_data='remove_delivered')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_start_msg(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    logger.info(f'Новое сообщение: /start или /help. пользователь:{user_id}')

    users.add_user(user_id)

    update.message.reply_text('Этот бот может отслеживать посылки через сервис Почта России\n'
                              'Чтобы узнать где находится ваша посылка, просто введие номер отправления.\n'
                              'Техподдержка: телеграм t.me/dragon_np почта: dragonnp@yandex.ru',
                              reply_markup=get_keyboard_my_packages(),
                              disable_web_page_preview=True)


def send_package(update: Update, context: CallbackContext) -> None:
    barcode = update.message.text

    if update.effective_user.link is not None:
        __user = update.effective_user.link
    elif update.effective_user.full_name is not None and update.effective_user.full_name != '':
        __user = update.effective_user.full_name
    else:
        __user = update.effective_user.id

    logger.info(
        f'Отправка истории передвижения посылки. пользователь:{__user}, трек-номер:{barcode}')

    message = update.message.reply_text('🛳*Отслеживаю посылку...*', parse_mode=telegram.ParseMode.MARKDOWN)

    package = Package(barcode)
    output = format_helper.format_route_short(package, barcode)
    is_tracked = users.check_barcode(message.chat_id, barcode)

    message.edit_text(output,
                      reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=True),
                      parse_mode=telegram.ParseMode.MARKDOWN)


def route_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if 'show_all_route_' in query.data:
        return send_all_history(update, context)
    elif 'show_short_route_' in query.data:
        return all_history_to_short(update, context)
    elif 'add_to_tracked_' in query.data:
        return add_barcode_in_track(update, context)
    elif 'remove_from_tracked_' in query.data:
        return remove_barcode_in_track(update, context)
    elif 'remove_delivered' in query.data:
        return remove_delivered(update, context)


def send_all_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('show_all_route_', '')

    logger.debug(f'Отправка полной информации о трек-номере. трек-номер:{barcode}, пользователь:{query.from_user.id}')

    package = Package(barcode)

    output = format_helper.format_route(package, barcode)

    isTracked = users.check_barcode(query.from_user.id, barcode)
    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_track(barcode, is_tracked=isTracked, is_show_all_track=False),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def all_history_to_short(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('show_short_route_', '')

    logger.debug(f'Отправка базовой информации о трек-номере. пользователь:{query.from_user.id}, трек-номер:{barcode}')

    package = Package(barcode)
    output = format_helper.format_route_short(package, barcode)
    is_tracked = users.check_barcode(query.from_user.id, barcode)

    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=True),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def add_barcode_in_track(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode, is_show_all_track = query.data.replace('add_to_tracked_', '').split('_')
    is_show_all_track = is_show_all_track == '1'
    result = users.update_barcode(query.from_user.id, barcode)

    logger.debug(f'Добавление трек-номера в отслеживаемое. трек-номер:{barcode}, пользователь:{query.from_user.id}')

    query.edit_message_reply_markup(
        reply_markup=get_keyboard_track(barcode, is_tracked=result, is_show_all_track=is_show_all_track))


def remove_barcode_in_track(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    barcode, is_show_all_track = query.data.replace('remove_from_tracked_', '').split('_')
    is_show_all_track = is_show_all_track == '1'
    result = not users.update_barcode(query.from_user.id, barcode, remove=True)

    logger.debug(f'Удаление трек-номера в отслеживаемое. barcode:{barcode}, user:{query.from_user.id}')

    query.edit_message_reply_markup(
        reply_markup=get_keyboard_track(barcode, is_tracked=result, is_show_all_track=is_show_all_track))


def send_new_package(barcode: str, package: Package, user_id: int, bot):
    logger.debug(
        f'Отправка нового обновления. трек-номер:{barcode}, пользователь:{user_id}')

    output = format_helper.format_route_short(package, barcode)
    is_tracked = users.check_barcode(user_id, barcode)

    return bot.send_message(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN,
                            reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=True))


def get_text_my_packages(user_id: int):
    text = '🛳*Отслеживаемые посылки*\n\n'
    barcodes = users.get_barcodes(user_id)
    for curr_barcode in barcodes:
        package = Package(curr_barcode)

        history = format_helper.format_history(package.history[-1])
        if not history[0]:
            return 'Error', history[1]
        text += f'*{package.name} ({curr_barcode})*\n{history}\n\n'
    return text


def send_my_packages(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if update.effective_user.link is not None:
        __user = update.effective_user.link
    elif update.effective_user.full_name is not None and update.effective_user.full_name != '':
        __user = update.effective_user.full_name
    else:
        __user = update.effective_user.id

    logger.info(
        f'Отправка всех отправлений:{__user}')

    text = get_text_my_packages(user_id)

    if text[0] == 'Error':
        context.error = text[1]
        return error_callback(update, context)

    update.message.reply_text(text,
                              parse_mode=telegram.ParseMode.MARKDOWN,
                              reply_markup=get_keyboard_remove_delivered())


def remove_delivered(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    logger.debug(f'Удаление доставленных посылок. пользователь:{user_id}')

    edit_message = False
    barcodes = users.get_barcodes(user_id)
    for curr_barcode in barcodes:
        package = Package(curr_barcode)
        if package.is_delivered:
            users.update_barcode(user_id, curr_barcode, remove=True, save=False)
            edit_message = True
    users.save()

    text = get_text_my_packages(user_id)

    if text[0] == 'Error':
        context.error = text[1]
        return error_callback(update, context)

    if not edit_message:
        logger.debug(f'Доставленных посылок не обнаружено. пользователь:{user_id}')
        return

    query.edit_message_text(text,
                            parse_mode=telegram.ParseMode.MARKDOWN,
                            reply_markup=get_keyboard_remove_delivered())


def check_new_update(context: CallbackContext):
    logger.info('Началась проверка новый обновлений')

    _users = users.db
    _packages = barcodes_db.db
    _new_packages = {}
    _new_version_old_packages = {}

    for user_id in _users:
        barcodes = _users[user_id]['barcodes']

        for curr_barcode in barcodes:
            if curr_barcode in _new_packages:
                package = Package.from_json(_new_packages[curr_barcode], curr_barcode)
                send_new_package(barcode=curr_barcode, package=package, user_id=int(user_id),
                                 bot=context.bot)
                continue

            updated_package = Package.from_rpt(curr_barcode)
            if curr_barcode in _packages and updated_package.history == _packages[curr_barcode]['History']:
                if updated_package.features != _packages[curr_barcode]:
                    _new_version_old_packages[curr_barcode] = updated_package.features

                continue

            _new_packages[curr_barcode] = updated_package.features
            send_new_package(barcode=curr_barcode, package=updated_package, user_id=int(user_id),
                             bot=context.bot)
    _new_packages.update(_new_version_old_packages)
    barcodes_db.save_packages(_new_packages)


def error_callback(update: Update, context: CallbackContext):
    error: Exception = context.error

    logger.error(error)
    update.message.reply_text(
        'Произошла ошибка. '
        'Пожалуйста, свяжитесь со мной через телеграм t.me/dragon_np или через почту dragonnp@yandex.ru',
        reply_markup=get_keyboard_my_packages(),
        disable_web_page_preview=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create the Updater and pass it your bot token.
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', send_start_msg))
    dispatcher.add_handler(CommandHandler('help', send_start_msg))
    dispatcher.add_handler(MessageHandler(Filters.text('Показать отслеживаемое'), send_my_packages))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_package))
    dispatcher.add_handler(CallbackQueryHandler(route_callback))
    dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    j: JobQueue = updater.job_queue
    j.run_daily(check_new_update, days=(0, 1, 2, 3, 4, 5, 6),
                time=datetime.time(hour=10, minute=00, second=00))

    j.run_once(check_new_update, 30)

    logger.info('Бот работает')
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
