def get_route(history_track):
    history = history_track.historyRecord[0]
    travel_to = history.AddressParameters.DestinationAddress.Description
    travel_from = history.AddressParameters.CountryFrom.NameRU

    return travel_from + ' → ' + travel_to


def get_sender(history_track):
    history = history_track.historyRecord[0]
    return history.UserParameters.Sndr


def get_recipient(history_track):
    history = history_track.historyRecord[0]
    return history.UserParameters.Rcpn


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
        return ''


def get_mass_item(history_record):
    try:
        return history_record.ItemParameters.Mass
    except AttributeError:
        return 0


def get_date_operation(history_record):
    return history_record.OperationParameters.OperDate.strftime('%m.%d.%Y %H:%M')


def get_operation(history_record):
    operation_parameters = history_record.OperationParameters

    if operation_parameters.OperAttr.Id != 0:
        operation = operation_parameters.OperAttr.Name
    else:
        operation = operation_parameters.OperType.Name

    return operation
