import refactor_track


def format_route_short(history_track, barcode):
    mass_item = ''

    for i in range(len(history_track.historyRecord) - 1, -1, -1):
        history = history_track.historyRecord[i]
        new_mass_item = refractor_track.get_mass_item(history)
        if new_mass_item != 0:
            mass_item = new_mass_item

    last = len(history_track.historyRecord) - 1
    history = history_track.historyRecord[last]
    history_travel = get_format(history, only_history=True)

    specs = get_specs(barcode, history_track, mass_item)
    output = specs + history_travel

    return output


def format_route(history_track, barcode):
    mass_item = ''
    history_travel = ''

    for i in range(len(history_track.historyRecord) - 1, -1, -1):
        history = history_track.historyRecord[i]
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
    operation_address = refractor_track.get_operation_address(history)

    if not only_history:
        new_mass_item = refractor_track.get_mass_item(history)
        if new_mass_item != 0:
            mass_item = new_mass_item

    history_travel += '*[' + refractor_track.get_date_operation(history) + ']*: '
    history_travel += refractor_track.get_operation(history)
    if operation_address != '':
        history_travel += ' (' + operation_address + ')'

    if not only_history:
        return mass_item, history_travel
    return history_travel


def get_specs(barcode, history_track, mass_item):
    specs = '🛳 Посылка *' + barcode + '*\n\n'

    route = refractor_track.get_route(history_track)
    sender = refractor_track.get_sender(history_track)
    recipient = refractor_track.get_recipient(history_track)

    specs += f'Маршурт: *{route}*\n'
    specs += f'Отправитель: *{sender}*\n'
    specs += f'Получатель: *{recipient}*\n'

    specs += 'Масса посылки: *' + str(mass_item) + ' гр. *\n\n'

    return specs
