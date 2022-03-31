from russian_post_tracking.soap import RussianPostTracking
import logging
from database import BarcodesDB


class Package:
    logger = logging.getLogger('package')

    def __init__(self, barcode_number, rpt_login, rpt_password, path_db, logger_level):
        self.db = BarcodesDB(path_db, logger_level)
        features = self.db.get_history_track(barcode_number)

        if features is None:
            result_suds = RussianPostTracking(barcode_number, rpt_login, rpt_password).get_history()
            self.__transform(result_suds)
            self.db.add_barcode(barcode_number, self.features)
        else:
            self.__set_variables(features)

    def __transform(self, result_suds):
        _suds = result_suds['historyRecord']

        res = {'History': [], 'Mass': 0, 'SenderFullName': '', 'RecipientFullName': '', 'DestinationAddress': '',
               'DestinationIndex': '', 'SenderAddress': '', 'CountryFrom': '', 'CountryTo': '', 'Name': ''}

        for point in _suds:

            curr_point = {}
            for key in point:
                suds = key[1]
                if key[0] == 'AddressParameters':
                    if 'DestinationAddress' in suds:
                        res['DestinationAddress'] = suds['DestinationAddress']['Description']

                    if 'DestinationAddress' in suds and 'Index' in suds['DestinationAddress']:
                        res['DestinationIndex'] = suds['DestinationAddress']['Index']

                    if 'CountryFrom' in suds:
                        res['SenderAddress'] = suds['CountryFrom']['NameRU']

                    if 'CountryFrom' in suds:
                        res['CountryFrom'] = suds['CountryFrom']['NameRU']

                    if 'CountryOper' in suds:
                        res['CountryTo'] = suds['CountryOper']['NameRU']

                    if 'OperationAddress' in suds:
                        curr_point['StatusAddress'] = suds['OperationAddress']['Description']
                    else:
                        curr_point['StatusAddress'] = ''

                    if 'OperationAddress' in suds and 'Index' in suds['OperationAddress']:
                        curr_point['StatusIndex'] = suds['OperationAddress']['Index']
                    else:
                        curr_point['StatusIndex'] = ''

                if key[0] == 'ItemParameters':
                    if 'ComplexItemName' in suds:
                        res['Name'] = suds['ComplexItemName']

                    if 'Mass' in suds:
                        res['Mass'] = int(suds['Mass'])

                if key[0] == 'OperationParameters':
                    if 'OperAttr' in suds and 'Name' in suds['OperAttr']:
                        curr_point['Status'] = suds['OperAttr']['Name']
                    elif 'OperType' in suds and 'Name' in suds['OperType']:
                        curr_point['Status'] = suds['OperType']['Name']
                    else:
                        curr_point['Status'] = ''

                    if 'OperDate' in suds:
                        curr_point['Date'] = suds['OperDate'].strftime('%d.%m.%Y %H:%M')
                    else:
                        curr_point['Date'] = ''

                    if 'Mass' in suds:
                        res['Mass'] = int(suds['Mass'])

                if key[0] == 'UserParameters':
                    if 'Sndr' in suds and not (suds['Sndr'] is None):
                        res['SenderFullName'] = suds['Sndr']

                    if 'Rcpn' in suds and not (suds['Rcpn'] is None):
                        res['RecipientFullName'] = suds['Rcpn']

            res['History'].append(curr_point)

        self.__set_variables(res)

    def __set_variables(self, features):
        self.features = features
        self.history = features['History']
        self.mass = features['Mass']
        self.sender_fullname = features['SenderFullName']
        self.recipient_fullname = features['RecipientFullName']
        self.destination_address = features['DestinationAddress']
        self.destination_index = features['DestinationIndex']
        self.sender_address = features['SenderAddress']
        self.country_from = features['CountryFrom']
        self.country_to = features['CountryTo']
        self.name = features['Name']
