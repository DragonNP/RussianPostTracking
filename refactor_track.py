import logging

logger = logging.getLogger('Refactor track')


def get_route(history_track):
    try:
        history = history_track.historyRecord[0]
        travel_to = history.AddressParameters.DestinationAddress.Description
        travel_from = history.AddressParameters.CountryFrom.NameRU
        return travel_from + ' → ' + travel_to
    except AttributeError:
        logger.error(f'Not found route. History track: {history_track}')
        return ''


def get_sender(history_track):
    try:
        history = history_track.historyRecord[0]
        return history.UserParameters.Sndr
    except AttributeError:
        logger.error(f'Not found sender. History track: {history_track}')
        return ''


def get_recipient(history_track):
    try:
        history = history_track.historyRecord[0]
        return history.UserParameters.Rcpn
    except AttributeError:
        logger.error(f'Not found recipient. History track: {history_track}')
        return None


def get_operation_address(history_record):
    address_parameters = history_record.AddressParameters
    try:
        description = address_parameters.OperationAddress.Description

        try:
            index = address_parameters.OperationAddress.Index
            return description + ', ' + index

        except AttributeError:
            return description
    except AttributeError:
        logger.error(f'Not found operation address')
        return ''


def get_mass_item(history_record):
    try:
        return history_record.ItemParameters.Mass
    except AttributeError:
        return 0


def get_date_operation(history_record):
    return history_record.OperationParameters.OperDate.strftime('%m.%d.%Y %H:%M')


def get_operation(history_record):
    try:
        operation_parameters = history_record.OperationParameters

        if operation_parameters.OperAttr.Id != 0:
            operation = operation_parameters.OperAttr.Name
        else:
            operation = operation_parameters.OperType.Name

        return operation
    except AttributeError:
        return None
