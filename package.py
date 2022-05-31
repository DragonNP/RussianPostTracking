from russian_post_tracking.soap import RussianPostTracking
from const_variables import *
from database import BarcodesDB

barcodes_db = BarcodesDB()

logger = logging.getLogger('package')


class Package:

    def __init__(self, barcode_number):
        self.db = barcodes_db
        features = self.db.get_package(barcode_number)

        if features is None:
            result_suds = RussianPostTracking(barcode_number, RPT_LOGIN, RPT_PASSWORD).get_history()
            res = Package.suds_to_json(result_suds)
            self.__set_variables(res)
            self.db.add_barcode(barcode_number, self.features)
        else:
            self.__set_variables(features)

    @classmethod
    def from_suds(cls, suds, barcode_number):
        features = Package.suds_to_json(suds)
        return cls.from_json(features, barcode_number)

    @classmethod
    def from_json(cls, features, barcode_number):
        cls.barcode = barcode_number
        cls.features = features
        cls.history = features['History']
        cls.mass = features['Mass']
        cls.sender_fullname = features['SenderFullName']
        cls.recipient_fullname = features['RecipientFullName']
        cls.destination_address = features['DestinationAddress']
        cls.destination_index = features['DestinationIndex']
        cls.sender_address = features['SenderAddress']
        cls.country_from = features['CountryFrom']
        cls.country_to = features['CountryTo']
        cls.name = features['Name']
        cls.price = features['Price']
        cls.is_delivered = features['IsDelivered']

        return cls

    @classmethod
    def from_rpt(cls, barcode_number):
        result_suds = RussianPostTracking(barcode_number, RPT_LOGIN, RPT_PASSWORD).get_history()
        return Package.from_suds(result_suds, barcode_number)

    @staticmethod
    def suds_to_json(result_suds):
        res = {'History': [], 'Mass': 0, 'SenderFullName': '', 'RecipientFullName': '', 'DestinationAddress': '',
               'DestinationIndex': '', 'SenderAddress': '', 'CountryFrom': '', 'CountryTo': '', 'Name': '', 'Price': 0,
               'IsDelivered': False}

        if not ('historyRecord' in result_suds):
            logger.debug('Результат запроса пустой')
            return res

        _suds = result_suds['historyRecord']
        for point in _suds:

            curr_point = {'StatusAddress': '', 'StatusIndex': '', 'Status': '', 'Date': ''}
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

                    if 'OperationAddress' in suds and 'Description' in suds['OperationAddress'] and \
                            suds['OperationAddress']['Description'] is not None:
                        curr_point['StatusAddress'] = suds['OperationAddress']['Description']

                    if 'OperationAddress' in suds and 'Index' in suds['OperationAddress']:
                        curr_point['StatusIndex'] = suds['OperationAddress']['Index']

                if key[0] == 'ItemParameters':
                    if 'ComplexItemName' in suds:
                        res['Name'] = suds['ComplexItemName']

                    if 'Mass' in suds:
                        res['Mass'] = int(suds['Mass'])

                if key[0] == 'OperationParameters':
                    if 'Id' in suds['OperType'] and suds['OperType']['Id'] == 2:
                        res['IsDelivered'] = True

                    if 'Name' in suds['OperAttr']:
                        curr_point['Status'] = suds['OperAttr']['Name']
                    elif 'OperType' in suds and 'Name' in suds['OperType']:
                        curr_point['Status'] = suds['OperType']['Name']

                    if 'OperDate' in suds:
                        curr_point['Date'] = suds['OperDate'].strftime('%d.%m.%Y %H:%M')

                    if 'Mass' in suds:
                        res['Mass'] = int(suds['Mass'])

                if key[0] == 'UserParameters':
                    if 'Sndr' in suds and not (suds['Sndr'] is None):
                        res['SenderFullName'] = suds['Sndr']

                    if 'Rcpn' in suds and not (suds['Rcpn'] is None):
                        res['RecipientFullName'] = suds['Rcpn']

                if key[0] == 'FinanceParameters':
                    if 'Value' in suds:
                        res['Price'] = int(suds['Value'])

            res['History'].append(curr_point)

        return res

    @staticmethod
    def get_saved_packages():
        return barcodes_db.db

    @staticmethod
    def save_new_packages(packages):
        return barcodes_db.save_packages(packages)

    def save(self):
        self.db.update_package(self.barcode, self.features)

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
        self.price = features['Price']
        self.is_delivered = features['IsDelivered']
