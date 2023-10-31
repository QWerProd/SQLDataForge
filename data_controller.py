import os
from error_catcher import ErrorCatcher
import sqlite3

# Импорты для параметров
from datetime import datetime

app_conn = sqlite3.connect('app/app.db')
catcher = ErrorCatcher()


class DataController:

    @staticmethod
    def SetDatabases() -> list:
        """Читает папку data/ и вносит сведения о пБД в сБД."""
        db_count = [0, 0]
        app_curs = app_conn.cursor()
        templist = app_curs.execute("SELECT dbname FROM t_databases").fetchall()
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
        app_curs.close()
        return db_count

    @staticmethod
    def GetDatabases(short=True) -> list:
        """Возвращает список пБД из сБД."""
        databases = []

        app_curs = app_conn.cursor()
        if short:
            dblist = app_curs.execute("SELECT dbname FROM t_databases").fetchall()
            for dbname in dblist:
                databases.append(dbname[0])
        else:
            dblist = app_curs.execute("SELECT dbname, field_name, path, description FROM t_databases").fetchall()
            for dbitem in dblist:
                databases.append(dbitem)

        app_curs.close()
        return databases     

    @staticmethod
    def GetTablesFromDB() -> dict:
        """Возвращает словарь с именами таблиц базы данных из специальной таблицы t_cases_info"""
        all_tables = {}
        databases = {}
        result = app_conn.execute("SELECT dbname, path FROM t_databases").fetchall()
        for unit in result:
            databases[unit[0]] = unit[1]

        for database, path in databases.items():
            conn = sqlite3.connect(path + '\\' + database)
            cursor = conn.cursor()
            tables = cursor.execute(f"""SELECT table_name, column_name, column_type, column_code FROM t_cases_info ORDER BY posid;""").fetchall()

            list_tables = []
            for item in tables:
                list_tables.append(f"{item[0]}:{item[1]}:{item[2]}:{item[3]}")

            all_tables[database] = list_tables
            cursor.close()
            conn.close()
        
        return all_tables

    @staticmethod
    def GetDBFromTables(tables: list) -> tuple:
        """Принимает список таблиц, возвращает список баз данных, в которых они присутствуют"""
        all_tables = DataController.GetTablesFromDB()
        databases = []
        for key, value in all_tables.items():
            for item_main in value:
                if key in databases:
                    break
                for item in tables:
                    if item_main in item:
                        databases.append(key)
                        break

        return tuple(databases)

    @staticmethod
    def ParamChanger(param: str) -> str:
        """Переданный параметр возвращает исполняемый код для этого параметра"""

        curs = app_conn.cursor()
        param_name = curs.execute(f"SELECT param_value FROM t_params WHERE param_name = '{param}'").fetchone()
        if param_name is None:
            return catcher.error_message('E002')
        else:
            return eval(param_name[0])