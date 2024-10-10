import re
import os
import uuid

from data_controller import DataController as DC
from app_parameters import APP_PARAMETERS, APPLICATION_PATH
import sqlite3
import random as rd

# Импорты для генераторов
import datetime


class SQLGenerator:

    app_conn = sqlite3.Connection
    is_simple_mode = bool
    queryrow1 = ""
    queryrow2 = []
    table_name = ""
    new_table_info = {}
    rows_count = 0
    added_items = []
    cols = []
    columns_info = []
    indexes = []
    column_order = {}
    is_format_columns = bool
    session_uuid = ""

    class RGenerator:
        """Базовый класс типа генератора"""

        datalist: list
        cursor: sqlite3.Cursor
        table_info: dict
        is_format_columns: bool
        session_uuid: str

        def __init__(self, cursor: sqlite3.Cursor, table: list, is_format_columns: bool = True, session_uuid: str = None):
            """Инициализация генератора

            Args:
                cursor (sqlite3.Cursor): Курсор к БД
                table (list): Сведения о таблице (имя БД, имя таблицы, имя столбца, код генератора, тип столбца)
                is_format_columns (bool, optional): Необходимо ли форматировать генерируемые значения. Defaults to True.
                session_uuid (str): UUID сессии генерации
            """
            self.datalist = []
            self.cursor = cursor
            self.table_info = table
            self.is_format_columns = is_format_columns
            self.session_uuid = session_uuid

        def generate_data(self, row_count: int) -> list:
            """Генерация списка с определенным количеством строк данных"""
            pass

        def format_value(self, value: str) -> str:
            """Форматирует значение в соответствии с переданным типом"""
            formatted_value = ''
            try:
                if self.table_info[4] in ('text-value', 'date-value'):
                    formatted_value = f"'{value}'"
                else:
                    formatted_value = f"{value}"

                return formatted_value

            except ValueError:
                raise ColumnTypeNotAllowedError(self.table_info[2], self.table_info[4])

        def get_datalist(self) -> list:
            return self.datalist

    class RSetGenerator(RGenerator):

        def __init__(self, cursor: sqlite3.Cursor, table: list, is_format_columns: bool = True, session_uuid: str = None):
            super().__init__(cursor, table, is_format_columns)

        def generate_data(self, row_count: int) -> list:
            data = list(map(lambda x: x[0], self.cursor.execute(f"""SELECT "{self.table_info[2]}"
                                                                    FROM "{self.table_info[1]}"
                                                                    WHERE "{self.table_info[2]}" IS NOT NULL;""").fetchall()))
            for i in range(row_count):
                value = rd.choice(data)
                if self.is_format_columns:
                    value = super().format_value(value)
                self.datalist.append(value)

            return self.datalist

    class RValueGenerator(RGenerator):

        def __init__(self, cursor: sqlite3.Cursor, table: list, is_format_columns: bool = True, session_uuid: str = None):
            super().__init__(cursor, table, is_format_columns)

        def generate_data(self, row_count: int) -> list:
            data = self.cursor.execute(f"""SELECT min_value, max_value
                                           FROM "{self.table_info[1]}";""").fetchone()
            minvalue = int(data[0])
            maxvalue = int(data[1])

            for i in range(row_count):
                if self.is_format_columns:
                    value = super().format_value(rd.randint(minvalue, maxvalue))
                else:
                    value = rd.randint(minvalue, maxvalue)
                self.datalist.append(value)

            return self.datalist

    class RDateGenerator(RGenerator):

        def __init__(self, cursor: sqlite3.Cursor, table: list, is_format_columns: bool = True, session_uuid: str = None):
            super().__init__(cursor, table, is_format_columns)

        def generate_data(self, row_count: int) -> list:
            data = self.cursor.execute(f"""SELECT minvalue, maxvalue, min_day, min_month * 30, min_year * 365, max_day, max_month * 30, max_year * 365
                                           FROM "{self.table_info[1]}";""").fetchone()

            # Обработка минимального значения
            mindate = data[0]
            maxdate = data[1]
            min_substract = sum(data[2:5])
            max_substract = sum(data[5:])
            try:
                mindate = datetime.datetime.strptime(mindate, '%d.%m.%Y')
            except ValueError:
                mindate = DC.ParamChanger(mindate)
            mindate = mindate - datetime.timedelta(days=min_substract)

            # Обработка максимального значения
            try:
                maxdate = datetime.datetime.strptime(maxdate, '%d.%m.%Y')
            except ValueError:
                maxdate = DC.ParamChanger(maxdate)
            maxdate = maxdate - datetime.timedelta(days=max_substract)

            for i in range(row_count):

                # Выбор рандомного дня из промежутка
                days = (datetime.datetime(maxdate.year, maxdate.month, maxdate.day) - datetime.datetime(mindate.year, mindate.month, mindate.day)).days
                rnd_day = rd.randint(0, days)

                # Генерация даты
                gen_date = datetime.datetime.strftime(mindate + datetime.timedelta(days=rnd_day), APP_PARAMETERS['FORMAT_DATE'])
                if self.is_format_columns:
                    value = super().format_value(gen_date)
                else:
                    value = gen_date
                self.datalist.append(value)

            return self.datalist

    class RChainGenerator(RGenerator):
        """Генератор сбора строки из случайных значений каждого столбца таблицы"""

        def __init__(self, cursor: sqlite3.Cursor, table: list, is_format_columns: bool = True, session_uuid: str = None):
            super().__init__(cursor, table, is_format_columns)

        def generate_data(self, row_count: int) -> list:
            # Получение имен столбцов таблицы
            data = self.cursor.execute(f"""SELECT sql FROM sqlite_master WHERE tbl_name = '{self.table_info[1]}';""").fetchone()[0]
            pattern = r'"([^"]+)"'
            column_names = re.findall(pattern, data)

            # Отсеивание имени таблицы и столбца ID
            while True:
                if self.table_info[1] in column_names:
                    column_names.remove(self.table_info[1])
                if "id" in column_names:
                    column_names.remove("id")
                else:
                    break
            
            # Отбираем все строки из отсеянных столбцов
            column_values = []
            for column in column_names:
                values = list(map(lambda x: x[0], self.cursor.execute(f"""SELECT "{column}"
                                                                          FROM "{self.table_info[1]}"
                                                                          WHERE "{column}" IS NOT NULL;""").fetchall()))
                column_values.append(values)

            for i in range(row_count):

                # Поочередное получение данных
                datarow = ""
                for column_value in column_values:
                    item = rd.choice(column_value)
                    datarow += item

                if self.is_format_columns:
                    value = super().format_value(datarow)
                else:
                    value = datarow
                self.datalist.append(value)

            return self.datalist
    
    class RowIDSetGenerator(RGenerator):

        def __init__(self, cursor: sqlite3.Cursor, table: list, is_format_columns: bool = True, session_uuid: str = None):
            rowid_seed = session_uuid.join((table[0], table[1]))
            super().__init__(cursor, table, is_format_columns, rowid_seed)

        def generate_data(self, row_count: int) -> list:
            data = list(map(lambda x: x[0], self.cursor.execute(f"""SELECT "{self.table_info[2]}"
                                                                    FROM "{self.table_info[1]}";""").fetchall()))
            
            rd.seed(self.session_uuid)
            for i in range(row_count):
                row_number = rd.randint(0, len(data) - 1)
                if self.is_format_columns:
                    value = super().format_value(data[row_number])
                else:
                    value = data[row_number]
                self.datalist.append(value)

            return self.datalist

    def __init__(self, app_conn: sqlite3.Connection, rows_count: int, added_items: list, columns_info: list,
                 table_info: dict = None, indexes: list = None, is_simple_mode: bool = False, is_format_columns: bool = True):
        self.app_conn = app_conn
        self.rows_count = rows_count
        self.queryrow2.clear()
        self.cols.clear()
        self.columns_info = columns_info
        self.added_items = added_items
        self.is_format_columns = is_format_columns
        self.is_simple_mode = is_simple_mode
        self.indexes = indexes
        if table_info is not None:
            for key, value in table_info.items():
                self.table_name = key
                self.new_table_info = value
        else:
            self.new_table_info = {
                'is_id_create': False
            }

        i = 0
        for item in added_items:
            self.column_order[item] = i
            i += 1

        # Генерация UUID для конкретной сессии генерации данных
        self.session_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(datetime.datetime.now())))

    def CreateHeader(self):
        self.queryrow1 += f"""INSERT INTO {('"' + self.new_table_info['schema_name'] + '".') if self.new_table_info['schema_name'] != '' else ''}"{self.table_name}" """
        col_names = []
        if self.new_table_info['is_id_create']:
            col_names.append('id')
        for columns in self.columns_info:
            col_names.append(columns['column_name'])
        res = '", "'.join(col_names)
        self.queryrow1 += f'("{res}")'

    def CreateTable(self) -> str:
        query_createtable = f"""CREATE TABLE {('"' + self.new_table_info['schema_name'] + '".') if self.new_table_info['schema_name'] != '' else ''}"{self.table_name}" (\n    """
        items = []
        if self.new_table_info['is_id_create']:
            items.append(f'"id" INTEGER NOT NULL PRIMARY KEY\n')
        for colinfo in self.columns_info:
            items.append(f""""{colinfo['column_name']}" {colinfo['column_type']} """
                         f"{'NOT NULL ' if colinfo['column_not_null'] else ''}{'UNIQUE' if colinfo['column_unique'] else ''} "
                         f"{'DEFAULT ' + colinfo['column_default'] if colinfo['column_default'] != '' else ''}\n")
        query_createtable += '   ,'.join(items) + ');'

        for colinfo in self.columns_info:
            if colinfo['column_comment'] != '':
                query_createtable += f"""\n\nCOMMENT ON COLUMN "{self.table_name}"."{colinfo['column_name']}"\nIS '{colinfo['column_comment']}';"""
        return query_createtable

    def CreateIndex(self, index_info: dict) -> str:
        index = (f"""CREATE {'UNIQUE ' if index_info['is_unique'] else ''}INDEX "{index_info['index_name']}"\n"""
                 f"""ON {('"' + self.new_table_info['schema_name'] + '".') if self.new_table_info['schema_name'] != '' else ''}"{self.table_name}"("{'","'.join(index_info['columns'])}")""")
        if index_info['condition'] == '':
            index += ';'
        else:
            index += index_info['condition']
            if not index_info['condition'].endswith(';'):
                index += ';'
        index += '\n'

        return index

    def GenerateValues(self, rows_count: int = None) -> dict:
        simp_conn = sqlite3.Connection
        list_of_dbs = []
        connects = []
        datadict = {}

        if rows_count is not None:
            self.rows_count = rows_count

        # Установка колонок
        if self.is_simple_mode:

            # Для simple_mode
            db_name = DC.GetDBFromTables([self.added_items[0], ])[0]
            db_path = DC.GetDatabasePath(db_name)
            with sqlite3.connect(db_path) as simp_conn:
                curs = simp_conn.cursor()

                table = curs.execute(f"""SELECT '{db_name}', table_name, column_name, gen_key, 'integer-value'
                                        FROM t_cases_info
                                        WHERE table_name = "{self.added_items[0]}"
                                        AND   column_name = "{self.added_items[1]}";""").fetchone()
                
                generator = generators.get(table[3])(curs, table, session_uuid=self.session_uuid)
                datadict[table[0] + ':' + table[1] + ':' + table[2] + ':' + table[4]] = generator.generate_data(self.rows_count)
                curs.close()    

        else:
            temp = []
            for table_item in self.added_items:
                temp.append(table_item.split(':')[0])
                list_of_dbs = list(set(temp))

            app_curs = self.app_conn.cursor()

            # Составление списка пБД (имя БД, путь/к/БД)
            query = (f"""SELECT dbname, path FROM t_databases
                         WHERE dbname IN ("{'","'.join(list_of_dbs)}");""")
            databases = app_curs.execute(query).fetchall()

            # Добавление столбца ID
            id_column = False
            if self.new_table_info['is_id_create']:
                increment = int(self.new_table_info['increment_start'])
                id_column = True
                if id_column:
                    row = []
                    for i in range(increment, self.rows_count + increment):
                        row.append(str(i))
                    datadict['id'] = row
                    # self.column_names.append('id')

            # Собираем краткие сведения о колонках для дальнейшей обработки
            temp_cols = []
            for colnames in self.added_items:
                temp_cols.append([colnames.split(':')[0], colnames.split(':')[1], colnames.split(':')[2], colnames.split(':')[4]])

            for database in databases:
                if not database[1].startswith('C:'):
                    database_path = os.path.join(APPLICATION_PATH, database[1])
                else:
                    database_path = database[1]

                # Открываем подключения к БД (коннект, имя БД)
                conn = sqlite3.connect(database_path)
                connects.append([conn, database[0]])
                cursor = conn.cursor()

                for item in temp_cols:
                    if item[0] == database[0]:
                        query = f"""SELECT '{item[0]}', table_name, column_name, gen_key, column_type
                                    FROM t_cases_info
                                    WHERE table_name = "{item[1]}"
                                    AND   column_name = "{item[2]}";"""
                        col_info = cursor.execute(query).fetchone()
                        self.cols.append(col_info)

            # Сортировка колонок в соответствии с порядком
            ordered_cols = []
            for item in self.added_items:
                for col in self.cols:
                    if f'{col[0]}:{col[1]}:{col[2]}' in item:
                        ordered_cols.append(col)
                        break
            self.cols = ordered_cols

            # Цикл генерации данных каждому столбцу
            for table in self.cols:

                # Устанавливаем текущее подключение и курсор к БД
                loc_conn = sqlite3.Connection
                for conn_row in connects:
                    if conn_row[1] == table[0]:
                        loc_conn = conn_row[0]
                        break

                cursor = loc_conn.cursor()

                # Инициализация необходимого класса коннектора
                generator = generators.get(table[3])(cursor, table, self.is_format_columns, self.session_uuid)
                datadict[table[0] + ':' + table[1] + ':' + table[2] + ':' + table[4]] = generator.generate_data(self.rows_count)

                cursor.close()

            # Закрываем все коннекты к пБД
            for conn in connects:
                conn[0].close()

        return datadict

    def CreateBody(self):
        # Получение сгенерируемых данных
        data = self.GenerateValues()

        datarow = []
        add_data = ''

        for i in range(self.rows_count):
            temp = []
            for value in data.values():
                temp.append(value[i])
            datarow.append(temp)

        for row in datarow:
            add_data = ', '.join(row)
            query = f'({add_data})\n'
            self.queryrow2.append(query)
            add_data = ''

    def BuildQuery(self, is_table=False) -> str:
        full_query = ''

        # Сборка запроса
        self.CreateBody()
        self.CreateHeader()

        # Создание таблицы
        if is_table:
            full_query += self.CreateTable() + '\n\n'

        # Создание индексов
        if len(self.indexes) > 0:
            indexes = []
            for index in self.indexes:
                indexes.append(self.CreateIndex(index))
            full_query += '\n'.join(indexes) + '\n'

        # Сборка значений
        full_query += self.queryrow1 + '\nVALUES '
        full_query += '      ,'.join(self.queryrow2)

        return full_query.rstrip('\n') + ';'


class ColumnTypeNotAllowedError(BaseException):

    column_name = str
    value_type = str

    def __init__(self, colname: str, coltype: str):
        self.column_name = colname
        self.value_type = coltype

    def __str__(self): return 'column type "{0}" is not enabled for this column: "{1}"'.format(self.value_type, self.column_name)


generators = {
    'RSet': SQLGenerator.RSetGenerator,
    'RValue': SQLGenerator.RValueGenerator,
    'RDate': SQLGenerator.RDateGenerator,
    'RChain': SQLGenerator.RChainGenerator,
    'RIDSet': SQLGenerator.RowIDSetGenerator
}
