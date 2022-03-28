import logging
import refactor_track

logger = logging.getLogger('format_helper')


def get_last_update(history_track):
    last = len(history_track['historyRecord']) - 1
    history = history_track['historyRecord'][last]

    last_update = refactor_track.get_date_operation(history)

    return last_update


def format_route_short(history_track, barcode):
    try:
        mass_item = ''

        for i in range(len(history_track['historyRecord']) - 1, -1, -1):
            history = history_track['historyRecord'][i]
            new_mass_item = refactor_track.get_mass_item(history)
            if new_mass_item != 0:
                mass_item = new_mass_item

        last = len(history_track['historyRecord']) - 1
        history = history_track['historyRecord'][last]
        history_travel = get_format(history, only_history=True)

        specs = get_specs(barcode, history_track, mass_item)
        output = specs + history_travel
        return output
    except AttributeError:
        logger.info(f'historyRecord не найден. История передвежний: {history_track}')
        return None


def format_route(history_track, barcode):
    mass_item = ''
    history_travel = ''

    for i in range(len(history_track['historyRecord']) - 1, -1, -1):
        history = history_track['historyRecord'][i]
        result = get_format(history)

        if result[0] is not None:
            mass_item = result[0]
        history_travel += result[1] + '\n'

    specs = get_specs(barcode, history_track, mass_item)
    output = specs + history_travel

    return output


def get_format(history, only_history=False):
    history_travel = ''
    mass_item = None
    operation_address = refactor_track.get_operation_address(history)

    if not only_history:
        new_mass_item = refactor_track.get_mass_item(history)
        if new_mass_item != 0:
            mass_item = new_mass_item

    history_travel += '*[' + refactor_track.get_date_operation(history) + ']*: '
    history_travel += refactor_track.get_operation(history)
    if operation_address != '':
        history_travel += ' (' + operation_address + ')'

    if not only_history:
        return mass_item, history_travel
    return history_travel


def get_specs(barcode, history_track, mass_item):
    specs = '🛳 Посылка *' + barcode + '*\n\n'

    route = refactor_track.get_route(history_track)
    sender = refactor_track.get_sender(history_track)
    recipient = refactor_track.get_recipient(history_track)

    specs += f'Маршурт: *{route}*\n'
    specs += f'Отправитель: *{sender}*\n'
    specs += f'Получатель: *{recipient}*\n'

    specs += 'Масса посылки: *' + str(mass_item) + ' гр. *\n\n'

    return specs
