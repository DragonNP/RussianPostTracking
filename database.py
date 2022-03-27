import os
import json
import logging

logger = logging.getLogger('database')


class UsersDB(object):
    def __init__(self, location):
        logger.debug('Инициализация базы данных пользователей')

        self.location = os.path.expanduser(location)
        self.load(self.location)

    def load(self, location):
        logger.debug('Загрузка базы данных')

        if os.path.exists(location):
            self.__load()
        else:
            logger.debug('Создание новой базы данных')
            self.db = {}
        return True

    def __load(self):
        logger.debug('Загрузка базы данных из файлв')
        self.db = json.load(open(self.location, 'r'))

    def __check_user(self, user_id: int):
        res = str(user_id) in self.db.keys()
        logger.debug(f'Проверка пользователе в базе данных. результат:{res}')
        return res

    def __dumpdb(self):
        logger.debug('Сохранение базы данных в файл')
        try:
            json.dump(self.db, open(self.location, 'w+'))
            return True
        except Exception as e:
            logger.error(e)
            return False

    def add_user(self, user_id):
        logger.debug(f'Создание пользователя. id пользователя:{user_id}')

        try:
            if self.__check_user(user_id):
                logger.debug(f'Пользователь уже создан. id пользователя:{user_id}')
                return False

            self.db[str(user_id)] = {'barcodes': [], 'time': ''}
            self.__dumpdb()
            return True
        except Exception as e:
            logger.error(f'Не удалось созранить пользователя. id пользователя:{user_id}', e)
            return False

    def update_time(self, user_id: int, time: str):
        logger.debug(f'Обновление времени. id пользователя:{user_id}, новое время:{time}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)

            self.db[str(user_id)]['time'] = time
            self.__dumpdb()
            return True
        except Exception as e:
            logger.error(f'Не удалось обновить время. id пользователя:{user_id}, новое время:{time}', e)
            return False

    def update_barcode(self, user_id: int, curr_barcode: str, remove=False):
        logger.debug(
            f'Обновление трек-номера. id пользователя:{user_id}, новый трек-номер:{curr_barcode}, удалить={remove}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)

            barcodes = self.db[str(user_id)]['barcodes']
            if remove:
                if not (curr_barcode in barcodes):
                    logger.debug(
                        f'Трек-номер не был сохранен. id пользователя:{user_id}, новый трек-номер:{curr_barcode}, удалить={remove}')
                    return False
                barcodes.remove(curr_barcode)
            else:
                if curr_barcode in barcodes:
                    logger.debug(
                        f'Трек-номер уже сохранен. id пользователя:{user_id}, новый трек-номер:{curr_barcode}, удалить={remove}')
                    return False
                barcodes.append(curr_barcode)
            self.db[str(user_id)]['barcodes'] = barcodes
            self.__dumpdb()
            return True
        except Exception as e:
            logger.error(
                f'Не удалось обновить трек-номер. id пользователя:{user_id}, новый трек-номер:{curr_barcode}, удалить={remove}',
                e)
            return False

    def check_barcode(self, user_id: int, curr_barcode: str):
        logger.debug(f'Проверка трек-номера. id пользователя:{user_id}, трек-номер:{curr_barcode}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)

            barcodes = self.db[str(user_id)]['barcodes']

            return curr_barcode in barcodes
        except Exception as e:
            logger.error(
                f'Не удалось проверить трек-номер. id пользователя:{user_id}, новый трек-номер:{curr_barcode}', e)
            return False

    def get(self, key):
        try:
            return self.db[key]
        except KeyError:
            print('No Value Can Be Found for ' + str(key))
            return False

    def resetdb(self):
        self.db = {}
        self.__dumpdb()
        return True
