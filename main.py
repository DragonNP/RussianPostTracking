from typing import Optional

from const_variables import *
import telegram
import datetime
import logging
import format_helper
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, \
    JobQueue, ConversationHandler
from package import Package
from database import UsersDB
from texts import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger('main')
logger.setLevel(GLOBAL_LOGGER_LEVEL)

users = UsersDB()

EDIT_NAME = range(1)


def get_keyboard_track(barcode, is_tracked=False, is_show_all_track=True):
    keyboard = []

    if is_show_all_track:
        keyboard.append([InlineKeyboardButton('Показать полный путь', callback_data='show_all_route_' + barcode)])
    else:
        keyboard.append(
            [InlineKeyboardButton('Показать последнее изменение', callback_data='show_short_route_' + barcode)])

    keyboard.append([InlineKeyboardButton('Редактировать название', callback_data='edit_name_' + barcode)])

    if is_tracked:
        keyboard.append([InlineKeyboardButton('Перестать отслеживать',
                                              callback_data=f'remove_from_tracked_{barcode}_{int(is_show_all_track)}')])
    else:
        keyboard.append(
            [InlineKeyboardButton('Отслеживать', callback_data=f'add_to_tracked_{barcode}_{int(is_show_all_track)}')])

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


def get_keyboard_rename():
    keyboard = [[InlineKeyboardButton('Назад', callback_data='back')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def send_start_msg(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    logger.info(f'Новое сообщение: /start или /help. пользователь:{user_id}')

    users.add_user(user_id)

    update.message.reply_text(TEXT_START,
                              reply_markup=get_keyboard_my_packages(),
                              disable_web_page_preview=True)


def send_package(update: Update, context: CallbackContext) -> None:
    barcode = update.message.text
    user_id = update.effective_user.id

    if update.effective_user.link is not None:
        __user = update.effective_user.link
    elif update.effective_user.full_name is not None and update.effective_user.full_name != '':
        __user = update.effective_user.full_name
    else:
        __user = user_id

    logger.info(
        f'Отправка истории передвижения посылки. пользователь:{__user}, трек-номер:{barcode}')

    message = update.message.reply_text('🛳*Отслеживаю посылку...*', parse_mode=telegram.ParseMode.MARKDOWN)

    package = Package(barcode)

    is_tracked, name = users.get_package_specs(user_id, barcode)
    output = format_helper.format_route_short(package, barcode, custom_name=name)

    message.edit_text(text=output,
                      reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=True),
                      parse_mode=telegram.ParseMode.MARKDOWN)


def route_callback(update: Update, context: CallbackContext) -> Optional[range]:
    query = update.callback_query

    if 'show_all_route_' in query.data:
        return send_all_history(update, context)
    elif 'show_short_route_' in query.data:
        return all_history_to_short(update, context)
    elif 'edit_name_' in query.data:
        return start_rename_package(update, context)
    elif 'add_to_tracked_' in query.data:
        return add_barcode_in_track(update, context)
    elif 'remove_from_tracked_' in query.data:
        return remove_barcode_in_track(update, context)
    elif 'remove_delivered' in query.data:
        return remove_delivered(update, context)


def send_all_history(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    barcode = query.data.replace('show_all_route_', '')

    logger.debug(f'Отправка полной информации о трек-номере. трек-номер:{barcode}, пользователь:{user_id}')

    package = Package(barcode)
    is_tracked, name = users.get_package_specs(user_id, barcode)
    output = format_helper.format_route(package, barcode, custom_name=name)

    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=False),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def all_history_to_short(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    barcode = query.data.replace('show_short_route_', '')

    logger.debug(f'Отправка базовой информации о трек-номере. пользователь:{user_id}, трек-номер:{barcode}')

    package = Package(barcode)
    is_tracked, name = users.get_package_specs(user_id, barcode)
    output = format_helper.format_route_short(package, barcode, custom_name=name)

    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=True),
                            parse_mode=telegram.ParseMode.MARKDOWN)


def start_rename_package(update: Update, context: CallbackContext) -> range:
    query = update.callback_query
    query.answer()

    barcode = query.data.replace('edit_name_', '')
    user_id = query.from_user.id

    logger.debug(f'Изменение названия посылки. пользователь:{user_id}, трек-номер:{barcode}')

    output = 'Введите название для этой посылки'

    context.user_data['rename_barcode'] = barcode
    context.user_data['msg_id'] = query.message.message_id
    query.edit_message_text(text=output,
                            reply_markup=get_keyboard_rename())
    return EDIT_NAME


def cancel_rename_package(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    barcode = context.user_data['rename_barcode']
    message_id = context.user_data['msg_id']

    del context.user_data['rename_barcode']
    del context.user_data['msg_id']

    logger.debug(f'Название посылки не было изменено. пользователь:{user_id}')

    package = Package(barcode)

    is_tracked, name = users.get_package_specs(user_id, barcode)
    output = format_helper.format_route_short(package, barcode, custom_name=name)

    context.bot.edit_message_text(text=output,
                                  chat_id=user_id,
                                  message_id=message_id,
                                  parse_mode=telegram.ParseMode.MARKDOWN,
                                  reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked,
                                                                  is_show_all_track=True))

    return ConversationHandler.END


def end_rename_package(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    name = update.message.text
    barcode = context.user_data['rename_barcode']
    del context.user_data['rename_barcode']

    users.rename_barcode(user_id, barcode, name)

    logger.debug(f'Название посылки изменено. пользователь:{user_id}, имя:{name}, трек-номер:{barcode}')

    update.message.reply_text('Название посылки изменено', reply_markup=get_keyboard_my_packages())

    return ConversationHandler.END


def add_barcode_in_track(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id

    barcode, is_show_all_track = query.data.replace('add_to_tracked_', '').split('_')
    is_show_all_track = is_show_all_track == '1'

    already_added = users.check_barcode(user_id=user_id, curr_barcode=barcode)
    if already_added:
        result = users.update_barcode(user_id=user_id, curr_barcode=barcode, tracked=True, save=True)
    else:
        result = users.add_barcode(user_id=user_id, curr_barcode=barcode, name='', tracked=True, save=True)

    logger.debug(f'Добавление трек-номера в отслеживаемое. трек-номер:{barcode}, пользователь:{user_id}')

    query.edit_message_reply_markup(
        reply_markup=get_keyboard_track(barcode, is_tracked=result, is_show_all_track=is_show_all_track))


def remove_barcode_in_track(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id

    barcode, is_show_all_track = query.data.replace('remove_from_tracked_', '').split('_')
    is_show_all_track = is_show_all_track == '1'
    result = not users.update_barcode(user_id=user_id, curr_barcode=barcode, tracked=False)

    logger.debug(f'Удаление трек-номера в отслеживаемое. barcode:{barcode}, user:{user_id}')

    query.edit_message_reply_markup(
        reply_markup=get_keyboard_track(barcode, is_tracked=result, is_show_all_track=is_show_all_track))


def send_new_package(barcode: str, package: Package, user_id: int, bot):
    logger.debug(
        f'Отправка нового обновления. трек-номер:{barcode}, пользователь:{user_id}')

    is_tracked, name = users.get_package_specs(user_id, barcode)
    output = format_helper.format_route_short(package, barcode, custom_name=name)

    try:
        res = bot.send_message(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN,
                               reply_markup=get_keyboard_track(barcode, is_tracked=is_tracked, is_show_all_track=True))
        print(res)
        return ''
    except telegram.error.Unauthorized:
        logger.info(f'Пользователь заблокировал бота. user_id:{user_id}')
        return 'blocked'


def get_text_my_packages(user_id: int):
    text = '🛳*Отслеживаемые посылки*\n\n'
    barcodes = users.get_barcodes(user_id)
    for curr_barcode in barcodes:
        if not barcodes[curr_barcode]['Tracked']:
            continue

        package = Package(curr_barcode)

        custom_name = users.get_package_specs(user_id, curr_barcode)[1]
        parcel_name = 'Посылка' if (not custom_name and not package.name) \
            else custom_name if custom_name else package.name

        text += f'*{parcel_name} ({curr_barcode})*\n'
        if len(package.history) > 0:
            history = format_helper.format_history(package.history[-1])
            if not history[0]:
                return 'Error', history[1]
            text += f'{history}\n\n'
        else:
            text += '\n'
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
        if not barcodes[curr_barcode]['Tracked']:
            continue

        package = Package(curr_barcode)
        if package.is_delivered:
            users.update_barcode(user_id=user_id, curr_barcode=curr_barcode, tracked=False, save=False)
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
    _packages = Package.get_saved_packages()
    _new_packages = {}
    _new_version_old_packages = {}
    _users_for_delete = []
    for user_id in _users:
        barcodes = _users[user_id]['barcodes']

        for curr_barcode in barcodes:
            if not barcodes[curr_barcode]['Tracked']:
                continue

            if curr_barcode in _new_packages:
                package = Package.from_json(_new_packages[curr_barcode], curr_barcode)
                res = send_new_package(barcode=curr_barcode, package=package, user_id=int(user_id),
                                       bot=context.bot)
                if res == 'blocked':
                    _users_for_delete.append(user_id)
                continue

            updated_package = Package.from_rpt(curr_barcode)
            if curr_barcode in _packages and updated_package.history == _packages[curr_barcode]['History']:
                if updated_package.features != _packages[curr_barcode]:
                    _new_version_old_packages[curr_barcode] = updated_package.features

                continue

            _new_packages[curr_barcode] = updated_package.features
            res = send_new_package(barcode=curr_barcode, package=updated_package, user_id=int(user_id),
                                   bot=context.bot)
            if res == 'blocked':
                _users_for_delete.append(user_id)

    for user_id in _users_for_delete:
        users.delete_user(user_id)
    _new_packages.update(_new_version_old_packages)
    Package.save_new_packages(_new_packages)


def error_callback(update: Update, context: CallbackContext):
    error: Exception = context.error

    logger.error(error, exc_info=True)
    if update is not None and update.message is not None:
        update.message.reply_text(TEXT_ERROR,
                                  reply_markup=get_keyboard_my_packages(),
                                  disable_web_page_preview=True)


def main() -> None:
    # Create the Updater and pass it your bot token.
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', send_start_msg))
    dispatcher.add_handler(CommandHandler('help', send_start_msg))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(route_callback)],
        states={
            EDIT_NAME: [MessageHandler(Filters.text & ~Filters.command, end_rename_package)]
        },
        fallbacks=[CallbackQueryHandler(cancel_rename_package, pattern='back')],
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(MessageHandler(Filters.text('Показать отслеживаемое'), send_my_packages))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, send_package))
    dispatcher.add_handler(CallbackQueryHandler(route_callback))
    dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    j: JobQueue = updater.job_queue
    j.run_daily(check_new_update, days=(0, 1, 2, 3, 4, 5, 6),
                time=datetime.time(hour=10, minute=00, second=00))

    # j.run_once(check_new_update, 30)

    logger.info('Бот работает')
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
