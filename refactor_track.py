import logging

logger = logging.getLogger('refactor_track')


def get_route(history_track):
    for i in range(0, len(history_track.historyRecord)):
        try:
            history = history_track.historyRecord[i]
            travel_to = history.AddressParameters.DestinationAddress.Description
            travel_from = history.AddressParameters.CountryFrom.NameRU
            return travel_from + ' → ' + travel_to
        except AttributeError:
            continue
    logger.error(f'Not found route. History track: {history_track}')
    return ''


def get_sender(history_track):
    for i in range(0, len(history_track.historyRecord)):
        try:
            history = history_track.historyRecord[i]
            sender = history.UserParameters.Sndr

            if sender is not None:
                return sender
        except AttributeError:
            continue
    logger.error(f'Not found sender. History track: {history_track}')
    return ''


def get_recipient(history_track):
    for i in range(0, len(history_track.historyRecord)):
        try:
            history = history_track.historyRecord[i]
            recipient = history.UserParameters.Rcpn

            if recipient is not None:
                return recipient
        except AttributeError:
            continue
    logger.error(f'Not found recipient. History track: {history_track}')
    return ''


def get_operation_address(history_record):
    address_parameters = history_record.AddressParameters
    try:
        try:
            description = address_parameters.OperationAddress.Description
        except AttributeError:
            description = address_parameters.CountryOper.NameRU

        try:
            index = address_parameters.OperationAddress.Index
            return description + ', ' + index

        except AttributeError:
            return description
    except AttributeError:
        logger.error(f'Not found operation operation')
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

        try:
            operation = operation_parameters.OperAttr.Name
        except AttributeError:
            operation = operation_parameters.OperType.Name

        return operation
    except AttributeError:
        return None
