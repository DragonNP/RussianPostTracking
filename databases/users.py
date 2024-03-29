import json

from const_variables import *


class UsersDB:
    logger = logging.getLogger('user_db')

    def __init__(self):
        self.db = {}
        self.logger.setLevel(GLOBAL_LOGGER_LEVEL)
        self.logger.debug('Инициализация базы данных пользователей')

        self.location = os.path.expanduser(PATH_TO_USERS_DATA_BASE)
        self.__load()

    def __load(self):
        self.logger.debug('Загрузка базы данных')

        if os.path.exists(self.location):
            self.logger.debug('Загрузка базы данных из файлв')
            self.db = json.load(open(self.location, 'r'))

        for user_id in self.db:
            if isinstance(self.db[user_id]['barcodes'], list):
                print('Hi')
                new = {}
                for barcode in self.db[user_id]['barcodes']:
                    new[barcode] = {'Name': '', 'Tracked': True}
                self.db[user_id]['barcodes'] = new

    def __check_user(self, user_id: int):
        res = str(user_id) in self.db.keys()
        self.logger.debug(f'Проверка пользователе в базе данных. результат:{res}')
        return res

    def __dump_db(self):

        self.logger.debug('Сохранение базы данных в файл')
        try:
            json.dump(self.db, open(self.location, 'w+'), ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def save(self):
        self.__dump_db()

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
            self.logger.error(f'Не удалось сохранить пользователя. id пользователя:{user_id}', e)
            return False

    def delete_user(self, user_id):
        self.logger.debug(f'Удаление пользователя. id пользователя:{user_id}')

        try:
            if not self.__check_user(user_id):
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                return False

            del self.db[str(user_id)]
            self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(f'Не удалось удалить пользователя. id пользователя:{user_id}', e)
            return False

    def add_barcode(self, user_id: int, curr_barcode: str, name: str = '', tracked=False, save=True):
        log_vars = f'id пользователя:{user_id}, новый трек-номер:{curr_barcode}, ' \
                   f'имя:{name}, отслеживаемое:{tracked}, сохранить:{save}'

        self.logger.debug(f'Добавление нового трек-номера. {log_vars}')
        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)
            if curr_barcode in self.db[str(user_id)]['barcodes']:
                self.logger.debug('Трек-номер уже добавлен')
                return False

            self.db[str(user_id)]['barcodes'][curr_barcode] = {'Name': name, 'Tracked': tracked}

            if save:
                self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(f'Не удалось добавить трек-номер', e, exc_info=True)
            return False

    def get_package_specs(self, user_id: int, barcode: str) -> (bool, str):
        log_vars = f'id пользователя:{user_id}, трек-номер:{barcode}'

        self.logger.debug(f'Получение название посылки и отслеживается ли она. {log_vars}')
        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)
                return False, ''
            if not (barcode in self.db[str(user_id)]['barcodes']):
                return False, ''

            tracked: bool = self.db[str(user_id)]['barcodes'][barcode]['Tracked']
            name: str = self.db[str(user_id)]['barcodes'][barcode]['Name']

            return tracked, name
        except Exception as e:
            self.logger.error(f'Не удалось добавить трек-номер', e, exc_info=True)
            return False, ''

    def update_barcode(self, user_id: int, curr_barcode: str, name: str = '', tracked: bool = None, save: bool = True):
        log_vars = f'id пользователя:{user_id}, новый трек-номер:{curr_barcode}, ' \
                   f'имя:{name}, отслеживаемое:{tracked}, сохранить:{save}'

        self.logger.debug(f'Добавление обновление трек-номера. {log_vars}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)
                return False

            barcode = self.db[str(user_id)]['barcodes'][curr_barcode]

            update = False
            if name != '':
                barcode['Name'] = name
                update = True
            if tracked is not None:
                barcode['Tracked'] = tracked
                update = True

            if not update:
                return False

            self.db[str(user_id)]['barcodes'][curr_barcode] = barcode

            if save:
                self.__dump_db()
            return True
        except Exception as e:
            self.logger.error(f'Не удалось обновить трек-номер. {log_vars}', e)
            return False

    def rename_barcode(self, user_id: int, barcode: str, name: str):
        log_vars = f'пользователь:{user_id}, трек-номер:{barcode}, новое имя:{name}'
        self.logger.debug(
            f'Изменение имени трек-номера. {log_vars}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)
                return False
            if not (barcode in self.db[str(user_id)]['barcodes']):
                self.logger.debug(
                    f'Трек-номер не сохранён в базе пользователей. {log_vars}')
                return self.add_barcode(user_id=user_id, curr_barcode=barcode, name=name)

            self.db[str(user_id)]['barcodes'][barcode]['Name'] = name
            self.save()
            return True
        except Exception as e:
            self.logger.error(
                f'Не удалось изменить имя трек-номера. {log_vars}',
                e)
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

    def get_barcodes(self, user_id: int):
        self.logger.debug(f'Получение всех трек-номеров. id пользователя:{user_id}')

        try:
            user_in_db = self.__check_user(user_id)
            if not user_in_db:
                self.logger.debug(f'Пользователь не найден. id пользователя:{user_id}')
                self.add_user(user_id)

            return self.db[str(user_id)]['barcodes']
        except Exception as e:
            self.logger.error(
                f'Не удалось получить все трек-номера. id пользователя:{user_id}', e)
            return False

    def get_count_users(self):
        self.logger.debug('Получение количество всех пользователей')
        try:
            return len(self.db)
        except Exception as e:
            self.logger.error(
                'Не удалось получить количество всех пользователей', e)
            return False

    def get_count_active_users(self):
        self.logger.debug('Получение количество активных пользователей')
        try:
            c = 0
            for user in self.db:
                if len(self.db[user]['barcodes']) >= 3:
                    c += 1
            return c
        except Exception as e:
            self.logger.error(
                'Не удалось получить количество активных пользователей', e)
            return False
