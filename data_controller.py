import os
import sys
from app.error_catcher import ErrorCatcher
from app_parameters import APP_PARAMETERS
import sqlite3

# Импорты для параметров
import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
elif __file__:
    BASE_DIR = os.path.dirname(__file__)

db_path = os.path.join(BASE_DIR, 'app\\app.db')
catcher = ErrorCatcher(APP_PARAMETERS['APP_LANGUAGE'])


class DataController:

    @staticmethod
    def SetDatabases() -> list:
        """Читает папку data/ и вносит сведения о пБД в сБД. Возвращает массив с количеством [успешных добавлений / ошибок]"""
        with sqlite3.connect(db_path) as app_conn:
            db_count = [0, 0]
            app_curs = app_conn.cursor()
            #try:
            templist = app_curs.execute("SELECT dbname FROM t_databases").fetchall()
            # except sqlite3.Error:
            #     catcher.error_message('E014')
            #     exit(14)
            dblist = []
            for dbname in templist:
                dblist.append(dbname[0])
            for root, dirs, files in os.walk(r"data/"):
                for file in files:
                    if file.endswith('.db') and dblist.count(file) == 0:
                        try:
                            app_curs.execute("INSERT INTO t_databases(dbname, path) VALUES ('" + file + "', '" + (root + file) + "');")
                            app_conn.commit()
                            db_count[0] += 1
                        except:
                            db_count[1] += 1
            return db_count

    @staticmethod
    def GetDatabases(short=True) -> list:
        """Возвращает список пБД с информацией из сБД.
        (для short=True - ('<uDB_name', ...))
        ('<uDB_name>', '<alias_name>', '<path/to/file>', '<description>', 'Y'/'N' - is_valid)"""
        with sqlite3.connect(db_path) as app_conn:
            databases = []

            app_curs = app_conn.cursor()
            if short:
                dblist = app_curs.execute("SELECT dbname FROM t_databases").fetchall()
                for dbname in dblist:
                    databases.append(dbname[0])
            else:
                dblist = app_curs.execute("SELECT dbname, field_name, path, description, is_valid FROM t_databases").fetchall()
                for dbitem in dblist:
                    databases.append(dbitem)

            app_curs.close()
            return databases

    @staticmethod
    def GetTablesFromDB() -> dict:
        """Возвращает словарь с именами таблиц базы данных из специальной таблицы t_cases_info.
        {'Person.db':
        ['t_person_man_names:last_name:Фамилия (М):text-value',
        't_person_man_names:first_name:Имя (М):text-value', ...],
        ...}"""
        with sqlite3.connect(db_path) as app_conn:
            all_tables = {}
            databases = {}
            try:
                result = app_conn.execute("SELECT dbname, path FROM t_databases").fetchall()
                for unit in result:
                    databases[unit[0]] = unit[1]
            except sqlite3.Error:
                pass

            curr_db = ''
            for database, path in databases.items():
                curr_db = database
                conn = sqlite3.Connection
                try:
                    if path.startswith('C:'):
                        conn = sqlite3.connect(path)
                    else:
                        conn = sqlite3.connect(os.path.join(BASE_DIR, path))
                    cursor = conn.cursor()
                    tables = cursor.execute(f"""SELECT table_name, column_name, column_code, column_type
                                                FROM t_cases_info
                                                ORDER BY posid;""").fetchall()

                    list_tables = []
                    for item in tables:
                        list_tables.append(f"{item[0]}:{item[1]}:{item[2]}:{item[3]}")

                    all_tables[database] = list_tables
                except sqlite3.OperationalError as e:
                    with sqlite3.connect(os.path.join(BASE_DIR, 'app/app.db')) as app_conn:
                        app_curs = app_conn.cursor()
                        app_curs.execute(f"""UPDATE t_databases
                                             SET    is_valid = 'N'
                                             WHERE  dbname = '{database}';""")
                        app_conn.commit()
                        app_curs.close()
                except sqlite3.Error as e:
                    if e.args[0] == 'no such table: t_cases_info':
                        app_curs = app_conn.cursor()
                        app_curs.execute(f"UPDATE t_databases "
                                         f"SET is_valid = 'N' "
                                         f"WHERE dbname = '{database}';")
                        app_conn.commit()
                        all_tables[database] = []

            return all_tables

    @staticmethod
    def GetDBFromTables(tables: list) -> list:
        """Принимает список таблиц, возвращает список баз данных, в которых они присутствуют"""
        all_tables = DataController.GetTablesFromDB()
        databases = []
        for key, value in all_tables.items():
            for item_main in value:
                if key in databases:
                    break
                for item in tables:
                    if item in item_main:
                        databases.append(key)
                        break

        return list(databases)

    @staticmethod
    def ParamChanger(param: str) -> str:
        """Переданный параметр возвращает исполняемый код для этого параметра"""
        with sqlite3.connect(db_path) as app_conn:
            curs = app_conn.cursor()
            param_name = curs.execute(f"SELECT param_value, param_type FROM t_params WHERE param_name = '{param}';").fetchone()
            if param_name is None:
                return catcher.error_message('E002')
            elif param_name[1] == 'GEN':
                return eval(param_name[0])
            else:
                return param_name[0]

    @staticmethod
    def GetListSimpleGens() -> dict:
        """Возвращает список всех простых генераторов"""
        with sqlite3.connect(db_path) as app_conn:
            gens = {}
            curs = app_conn.cursor()
            try:
                data = curs.execute(f"SELECT sg.gen_code, lt.text, 'simple'"
                                    f"FROM t_simple_gen as sg,"
                                    f"     t_lang_text as lt "
                                    f"WHERE sg.is_valid = 'Y' "
                                    f"AND   sg.gen_name = lt.label "
                                    f"AND   lt.lang = '{APP_PARAMETERS['APP_LANGUAGE']}';").fetchall()

                for datarow in data:
                    if not datarow[2] in gens:
                        gens[datarow[2]] = []
                    gens[datarow[2]].append((datarow[0], datarow[1]))

                return gens
            except sqlite3.Error:
                return list()

    @staticmethod
    def BuildDictOfGens() -> dict:
        """Собирает словарь со всеми полями для простого генератора.
        {'<Раздел>': [(<ключ>, '<подпись для меню>'), ...], ...}"""

        gens = DataController.GetListSimpleGens()
        user_gens = DataController.GetTablesFromDB()

        for database, values in user_gens.items():
            gens[database] = []
            for items in values:
                gen_key = ':'.join(items.split(':')[0:2])
                gens[database].append((gen_key, items.split(':')[2]))

        return gens

    @staticmethod
    def SetLangLabels(lang: str) -> dict:
        """Собирает словарь для подписей в приложении
        в зависимости от установленного языка"""
        with sqlite3.connect(db_path) as app_conn:
            curs = app_conn.cursor()
            try:
                text_labels = curs.execute(f"""SELECT label, text
                                               FROM t_lang_text
                                               WHERE lang = '{lang}';""").fetchall()

                text_dict = dict(text_labels)
                return text_dict
            except sqlite3.Error:
                return 1
            finally:
                curs.close()

    @staticmethod
    def GetDatabasePath(db_name: str) -> str:
        """Получает имя БД, возвращает путь к БД (полный)

        Args:
            db_name (str): Имя БД

        Returns:
            str: Путь к БД
        """
        pdb_path = ''
        with sqlite3.connect(db_path) as app_conn:
            curs = app_conn.cursor()
            pdb_path = curs.execute(f"SELECT path FROM t_databases WHERE dbname = '{db_name}';").fetchone()[0]
            curs.close()

        # Преобразуем путь к БД
        pdb_path = os.path.realpath(pdb_path)
        return pdb_path