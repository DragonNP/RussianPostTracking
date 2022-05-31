import logging
from package import Package

logger = logging.getLogger('format_helper')


def format_route_short(package: Package, barcode, custom_name=''):
    try:
        specs = get_specs(barcode, package, custom_name=custom_name)
        output = specs

        if len(package.history) > 1:
            history_travel = format_history(package.history[-1])
            output += history_travel

        return output
    except Exception as e:
        logger.error(e)
        return None


def format_route(package: Package, barcode, custom_name=''):
    history_travel = ''

    for point in package.history:
        history_travel = f'{format_history(point)}\n' + history_travel

    specs = get_specs(barcode, package, custom_name=custom_name)
    output = specs + history_travel

    return output


def format_history(point):
    try:
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
    except Exception as e:
        logger.error(e)
        return False, e


def get_specs(barcode, package: Package, custom_name: str = ''):
    specs = '🛳 '
    if custom_name != '':
        specs += f'*{custom_name}* ({barcode})'
    elif package.name != '':
        specs = f'*{package.name}* ({barcode})'
    else:
        specs = f'Посылка *{barcode}*'
    specs += '\n\n'

    sender = package.sender_fullname
    recipient = package.recipient_fullname
    mass = package.mass
    price = package.price

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
    if mass != 0:
        specs += f'Масса посылки: *{format_mass(mass)}*\n'
    if price != 0:
        specs += f'Объявленная ценность: *{format_price(price)}*\n'
    specs += '\n'

    return specs


def format_mass(mass: int):
    kg = mass // 1000
    gr = mass % 1000

    if kg > 0:
        res = str(kg)

        if gr > 0:
            if gr > 99:
                if gr % 10 > 4:
                    res += f',{gr // 10 + 1}'
                else:
                    res += f',{gr // 10}'
            else:
                res += f',{gr}'
        res += ' кг.'
    else:
        res = f'{gr} гр.'

    return res


def format_price(price: int):
    rubles = price // 100
    kopecks = price % 100

    res = '{:,.0f}'.format(rubles).replace(',', ' ')
    if kopecks > 0:
        if kopecks < 10:
            res += f',0{kopecks}'
        else:
            res += f',{kopecks}'
    res += ' руб.'

    return res
