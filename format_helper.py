import logging
from package import Package

logger = logging.getLogger('format_helper')


def format_route_short(package: Package, barcode):
    try:
        history_travel = format_history(package.history[-1])

        specs = get_specs(barcode, package, package.mass)
        output = specs + history_travel
        return output
    except Exception as e:
        logger.error(e)
        return None


def format_route(package: Package, barcode):
    history_travel = ''

    for point in package.history:
        history_travel += f'{format_history(point)}\n'

    specs = get_specs(barcode, package, package.mass)
    output = specs + history_travel

    return output


def format_history(point):
    formatted_history = ''

    if point['Date'] != '':
        formatted_history += f'*[{point["Date"]}]*: '
    if point['Status'] != '':
        formatted_history += point['Status']

    if point['StatusAddress'] != '' and point['StatusIndex'] != '':
        formatted_history += f' ({point["StatusAddress"]}, {point["StatusIndex"]})'
    elif point['StatusAddress'] != '' and point['StatusIndex'] == '':
        formatted_history += f' ({point["StatusAddress"]})'
    elif point['StatusAddress'] == '' and point['StatusIndex'] != '':
        formatted_history += f' ({point["StatusIndex"]})'

    return formatted_history


def get_specs(barcode, package: Package, mass_item: int):
    if package.name != '':
        specs = f'🛳 *{package.name}* ({barcode})\n\n'
    else:
        specs = f'🛳 Посылка *{barcode}*\n\n'

    sender = package.sender_fullname
    recipient = package.recipient_fullname

    if package.country_from != '' and package.destination_address != '':
        specs += f'Маршурт: *{package.country_from} → {package.destination_address}*\n'
    elif package.country_from != '' and package.destination_address == '':
        specs += f'От: *{package.country_from}*\n'
    elif package.country_from == '' and package.destination_address != '':
        specs += f'Прибывает в *{package.destination_address}*\n'

    if sender != '':
        specs += f'Отправитель: *{sender}*\n'
    if recipient != '':
        specs += f'Получатель: *{recipient}*\n'
    if mass_item != 0:
        specs += 'Масса посылки: *' + str(mass_item) + ' гр. *\n'
    specs += '\n'

    return specs
