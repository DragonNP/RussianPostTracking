import json

from const_variables import *


class BarcodesDB:
    logger = logging.getLogger('barcodes_db')

    def __init__(self):
        self.db = {}
        self.logger.setLevel(GLOBAL_LOGGER_LEVEL)
        self.logger.debug('Инициализация базы данных трек-номеров')

        self.location = os.path.expanduser(PATH_TO_PACKAGES_DATA_BASE)
        self.load(self.location)

    def load(self, location):
        self.logger.debug('Загрузка базы данных')

        if os.path.exists(location):
            self.__load()
        return True

    def __load(self):
        self.logger.debug('Загрузка базы данных из файлв')
        self.db = json.load(open(self.location, 'r'))

    def __dump_db(self, db=''):
        if db != '':
            self.db = db

        self.logger.debug('Сохранение базы данных в файл')
        try:
            json.dump(self.db, open(self.location, 'w+'), ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def save_packages(self, db):
        return self.__dump_db(db)

    def __check_barcode(self, barcode: str):
        res = barcode in self.db.keys()
        self.logger.debug(f'Проверка трек-номера в базе данных. результат:{res}')
        return res

    def add_barcode(self, barcode: str, history_track: json):
        self.logger.debug(f'Добавление трек-номера. трек-номер:{barcode}')

        try:
            if self.__check_barcode(barcode):
                self.logger.debug(f'Трек-номер уже добавлен. трек-номер:{barcode}')
                return False

            self.db[barcode] = history_track
            self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(f'Не удалось сохранить трек-номер. трек-номер:{barcode}', e)
            return False

    def get_package(self, barcode: str):
        self.logger.debug(f'Получение истории перемещений. трек-номер:{barcode}')
        try:
            if not self.__check_barcode(barcode):
                self.logger.debug(f'Трек-номер не сохранен в базе данных. трек-номер:{barcode}')
                return None

            return self.db[barcode]
        except Exception as e:
            self.logger.error(f'Не удалось получить историю отправлений. трек-номер:{barcode}', e)
            return None

    def update_package(self, barcode: str, features: json):
        self.logger.debug(f'Обновление истории передвижений трек-номера. трек-номер:{barcode}')

        try:
            if not self.__check_barcode(barcode):
                self.logger.debug(f'Трек-номер не добавлен. трек-номер:{barcode}')
                return False

            self.db[barcode] = features
            self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(f'Не удалось сохранить историю передвижений трек-номера. трек-номер:{barcode}', e)
            return False
