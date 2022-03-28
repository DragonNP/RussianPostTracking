import os
import json
import logging


class UsersDB:
    logger = logging.getLogger('user_db')

    def __init__(self, location, logger_level):
        self.db = {}
        self.logger.setLevel(logger_level)
        self.logger.debug('Инициализация базы данных пользователей')

        self.location = os.path.expanduser(location)
        self.load(self.location)

    def load(self, location):
        self.logger.debug('Загрузка базы данных')

        if os.path.exists(location):
            self.__load()
        return True

    def __load(self):
        self.logger.debug('Загрузка базы данных из файлв')
        self.db = json.load(open(self.location, 'r'))

    def __check_user(self, user_id: int):
        res = str(user_id) in self.db.keys()
        self.logger.debug(f'Проверка пользователе в базе данных. результат:{res}')
        return res

    def __dump_db(self):
        self.logger.debug('Сохранение базы данных в файл')
        try:
            json.dump(self.db, open(self.location, 'w+'))
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def add_user(self, user_id):
        self.logger.debug(f'Создание пользователя. id пользователя:{user_id}')

        try:
            if self.__check_user(user_id):
                self.logger.debug(f'Пользователь уже создан. id пользователя:{user_id}')
                return False

            self.db[str(user_id)] = {'barcodes': {}}
            self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(f'Не удалось созранить пользователя. id пользователя:{user_id}', e)
            return False

    def update_barcode(self, user_id: int, curr_barcode: str, last_update: str = None, remove=False):
        self.logger.debug(
            f'Обновление трек-номера. id пользователя:{user_id}, '
            f'новый трек-номер:{curr_barcode}, последнее обновление={last_update}, удалить={remove}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)

            barcodes = self.db[str(user_id)]['barcodes']
            if remove or last_update is None:
                barcodes.remove(curr_barcode)
            else:
                barcodes[curr_barcode] = last_update
            self.db[str(user_id)]['barcodes'] = barcodes
            self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(
                f'Не удалось обновить трек-номер. '
                f'id пользователя:{user_id}, новый трек-номер:{curr_barcode}, удалить={remove}', e)
            return False

    def check_barcode(self, user_id: int, curr_barcode: str):
        self.logger.debug(f'Проверка трек-номера. id пользователя:{user_id}, трек-номер:{curr_barcode}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)

            barcodes = self.db[str(user_id)]['barcodes']

            return curr_barcode in barcodes
        except Exception as e:
            self.logger.error(
                f'Не удалось проверить трек-номер. id пользователя:{user_id}, новый трек-номер:{curr_barcode}', e)
            return False

    def get_db(self):
        return self.db
