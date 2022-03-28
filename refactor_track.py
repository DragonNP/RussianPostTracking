import datetime
import logging
from suds.client import Client
import json as json_module

logger = logging.getLogger('refactor_track')


def recursion(json):
    for key in json:
        try:
            if 'suds' in str(json):
                if isinstance(json[key], bool):
                    json[key] = str(json[key])
                elif isinstance(json[key], datetime.datetime):
                    json[key] = json[key].strftime('%m.%d.%Y %H:%M')
                elif isinstance(json[key], str):
                    continue
                else:
                    json[key] = Client.dict(json[key])
                    json[key] = recursion(json[key])
        except Exception as e:
            logger.error(e)
    return json


def convert_to_json(history_track):
    if isinstance(history_track, str):
        return json_module.loads(history_track)

    json = Client.dict(history_track)
    for key in json:
        if isinstance(json[key], list):
            for i in range(len(json[key])):
                json[key][i] = Client.dict(json[key][i])
                json[key][i] = recursion(json[key][i])
    return json


def get_route(history_track):
    for i in range(0, len(history_track['historyRecord'])):
        try:
            history = history_track['historyRecord'][i]
            travel_to = history['AddressParameters']['DestinationAddress']['Description']
            travel_from = history['AddressParameters']['CountryFrom']['NameRU']
            return travel_from + ' → ' + travel_to
        except AttributeError:
            continue
    logger.error(f'Not found route. History track: {history_track}')
    return ''


def get_sender(history_track):
    for i in range(0, len(history_track['historyRecord'])):
        try:
            history = history_track['historyRecord'][i]
            sender = history['UserParameters']['Sndr']

            if sender is not None:
                return sender
        except AttributeError:
            continue
    logger.error(f'Not found sender. History track: {history_track}')
    return ''


def get_recipient(history_track):
    for i in range(0, len(history_track['historyRecord'])):
        try:
            history = history_track['historyRecord'][i]
            recipient = history['UserParameters']['Rcpn']

            if recipient is not None:
                return recipient
        except AttributeError:
            continue
    logger.error(f'Not found recipient. History track: {history_track}')
    return ''


def get_operation_address(history_record):
    address_parameters = history_record['AddressParameters']
    try:
        if 'OperationAddress' in address_parameters and \
                'Description' in address_parameters['OperationAddress']:
            description = address_parameters['OperationAddress']['Description']
        elif 'CountryOper' in address_parameters and \
                'NameRU' in address_parameters['CountryOper']:
            description = address_parameters['CountryOper']['NameRU']
        else:
            description = ''

        if 'OperationAddress' in address_parameters and \
                'Index' in address_parameters['OperationAddress']:
            index = address_parameters['OperationAddress']['Index']
            return description + ', ' + index
        return description
    except AttributeError:
        logger.error(f'Операция не найдена')
        return ''


def get_mass_item(history_record):
    if 'Mass' in history_record['ItemParameters']:
        return history_record['ItemParameters']['Mass']
    return 0


def get_date_operation(history_record):
    return history_record['OperationParameters']['OperDate']


def get_operation(history_record):
    try:
        operation_parameters = history_record['OperationParameters']

        if 'Name' in operation_parameters['OperAttr']:
            operation = operation_parameters['OperAttr']['Name']
        elif 'Name' in operation_parameters['OperType']:
            operation = operation_parameters['OperType']['Name']
        else:
            operation = ''

        return operation
    except AttributeError:
        return None
