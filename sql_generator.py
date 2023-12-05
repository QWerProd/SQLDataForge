import re

from data_controller import DataController as DC
import sqlite3
import random as rd

# Импорты для генераторов
import datetime

class SQLGenerator:
    app_conn = sqlite3.Connection
    is_simple_mode = bool
    queryrow1 = "INSERT INTO "
    queryrow2 = []
    table_name = ""
    new_table_info = {}
    rows_count = 0
    tables = []
    cols = []
    column_names = []
    indexes = []

    def __init__(self, app_conn: sqlite3.Connection, rows_count: int, tables: list, column_names: list,
                 table_info: dict = None, indexes: list = None) -> None:
        self.app_conn = app_conn

        self.rows_count = rows_count
        self.queryrow2.clear()
        self.cols.clear()
        self.column_names = column_names
        self.tables = tables
        self.is_simple_mode = True

        if table_info is not None:
            self.is_simple_mode = False
            for key, value in table_info.items():
                self.table_name = key
                self.new_table_info = value
        self.indexes = indexes

    def CreateHeader(self):
        self.queryrow1 += self.table_name
        col_names = []
        if self.new_table_info['is_id_create']:
            col_names.append('id')
        for columns in self.column_names:
            col_names.append(columns)
        res = ', '.join(col_names)
        self.queryrow1 += '(' + res + ')'

    def CreateTable(self) -> str:
        query_createtable = f'CREATE TABLE {self.table_name}(\n    '
        items = []
        if self.new_table_info['is_id_create']:
            items.append(f'id INTEGER NOT NULL\n')
        for i in range(len(self.cols)):
            items.append(f'{self.column_names[i]} {self.cols[i][4]}\n')
        query_createtable += '   ,'.join(items)
        if self.new_table_info['is_id_create']:
            query_createtable += '    PRIMARY KEY("id")\n'
        query_createtable += ');'
        return query_createtable

    def CreateIndex(self, index_info: dict) -> str:
        index = (f"CREATE {'UNIQUE ' if index_info['is_unique'] else ''}INDEX IF NOT EXISTS {index_info['index_name']}\n"
                 f"ON {self.table_name}({','.join(index_info['columns'])})")
        if index_info['condition'] == '':
            index += ';'
        else:
            index += index_info['condition']
            if not index_info['condition'].endswith(';'):
                index += ';'

        return index

    def GenerateValues(self) -> dict:
        simp_conn = sqlite3.Connection
        list_of_dbs = []
        connects = []
        datadict = {}
        temp = []
        for table_item in self.tables:
            temp.append(table_item.split(':')[0])
            list_of_dbs = list(set(temp))

        if self.is_simple_mode:
            db_name = DC.GetDBFromTables([list_of_dbs[0], ])[0]
            simp_conn = sqlite3.connect('data/' + db_name)
            curs = simp_conn.cursor()

            data = curs.execute(f"""SELECT '{db_name}', table_name, column_name, gen_key, column_type
                                    FROM t_cases_info
                                    WHERE table_name = "{list_of_dbs[0]}"
                                    AND   column_name = "{list_of_dbs[1]}";""").fetchone()
            self.cols.append(data)
        else:
            app_curs = self.app_conn.cursor()

            query = ('SELECT path FROM t_databases ' +
                     'WHERE dbname IN ("' + '","'.join(list_of_dbs) + '")')
            path_of_dbs = app_curs.execute(query).fetchall()
            databases = []
            for i in range(0, len(list_of_dbs)):
                databases.append((list_of_dbs[i], path_of_dbs[i][0]))

            id_column = False
            if self.new_table_info['is_id_create']:
                increment = int(self.new_table_info['increment_start'])
                id_column = True
                if id_column:
                    row = []
                    for i in range(increment, self.rows_count + increment):
                        row.append(i)
                    datadict['id'] = row
                    # self.column_names.append('id')

            for database in databases:
                conn = sqlite3.connect(database[1] + '\\' + database[0])
                connects.append([conn, database[0]])
                cursor = conn.cursor()
                temp_cols = []

                for colnames in self.tables:
                    temp_cols.append([colnames.split(':')[0], colnames.split(':')[1], colnames.split(':')[2]])

                for item in temp_cols:
                    if item[0] == database[0]:
                        query = f"""SELECT '{item[0]}', table_name, column_name, gen_key, column_type
                                    FROM t_cases_info
                                    WHERE table_name = "{item[1]}"
                                    AND   column_name = "{item[2]}";"""
                        temp_cols = cursor.execute(query).fetchone()
                        self.cols.append(temp_cols)

        # Generate data from all tables
        for table in self.cols:
            loc_conn = sqlite3.Connection
            if self.is_simple_mode:
                loc_conn = simp_conn
            else:
                for conn_row in connects:
                    if conn_row[1] == table[0]:
                        loc_conn = conn_row[0]
                        break
            cursor = loc_conn.cursor()

            # Getting maximum value of rows
            max_val = cursor.execute(f"SELECT COUNT(*) FROM {table[1]};").fetchone()[0]

            # Creating list of columns
            # self.column_names.append(table[1])

            datadict[table[0] + ':' + table[1] + ':' + table[2]] = list()

            for i in range(self.rows_count):
                # Getting random data from datasets
                if table[3] == 'RSet':
                    row_number = rd.randint(1, max_val)
                    data = cursor.execute(f"""SELECT {table[2]}
                                              FROM {table[1]}
                                              WHERE id = {row_number};""").fetchone()[0]
                    datadict[table[0] + ':' + table[1] + ':' + table[2]].append(data)
                elif table[3] == 'RValue':
                    data = cursor.execute(f"""SELECT min_value, max_value
                                                      FROM {table[1]};""").fetchone()
                    minvalue = int(data[0])
                    maxvalue = int(data[1])

                    datadict[table[0] + ':' + table[1] + ':' + table[2]].append(str(rd.randint(minvalue, maxvalue)))
                elif table[3] == 'RDate':
                    data = cursor.execute(f"""SELECT minvalue, minvalue_subtract, maxvalue, maxvalue_subtract
                                              FROM {table[1]};""").fetchone()
                    # Обработка минимального значения
                    mindate = data[0]
                    maxdate = data[2]
                    try:
                        mindate = datetime.datetime.strptime(mindate, '%Y-%m-%d')
                    except ValueError:
                        mindate = DC.ParamChanger(mindate)
                    mindate = mindate - datetime.timedelta(days=data[1] * 365)

                    # Обработка максимального значения
                    try:
                        maxdate = datetime.datetime.strptime(maxdate, '%Y-%m-%d')
                    except ValueError:
                        maxdate = DC.ParamChanger(maxdate)
                    maxdate = maxdate - datetime.timedelta(days=data[3] * 365)

                    # Выбор рандомного дня из промежутка
                    days = (maxdate - mindate).days
                    rnd_day = rd.randint(1, days)

                    # Генерация даты
                    datadict[table[0] + ':' + table[1] + ':' + table[2]].append(str(mindate + datetime.timedelta(days=rnd_day)))
                elif table[3] == 'RChain':
                    # Получение имен столбцов таблицы
                    data = cursor.execute(f"""SELECT sql FROM sqlite_master WHERE tbl_name = "{table[1]}";""").fetchone()[0]
                    pattern = r'"([^"]+)"'
                    column_names = re.findall(pattern, data)

                    # Отсеивание имени таблицы и столбца ID
                    while True:
                        if table[1] in column_names:
                            column_names.remove(table[1])
                        if "id" in column_names:
                            column_names.remove("id")
                        else:
                            break

                    # Поочередное получение данных
                    datarow = ""
                    for column in column_names:
                        max_val = int(cursor.execute(f"""SELECT COUNT("{column}") 
                                                     FROM {table[1]}
                                                     WHERE "{column}" IS NOT NULL;""").fetchone()[0])

                        item = cursor.execute(f"""SELECT {column} 
                                              FROM {table[1]} 
                                              WHERE id = {rd.randint(1, max_val)};""").fetchone()[0]
                        datarow += item

                    datadict[table[0] + ':' + table[1] + ':' + table[2]].append(datarow)
            cursor.close()

        # Закрываем все коннекты к пБД
        for conn in connects:
            conn[0].close()

        return datadict

    def CreateBody(self):
        # Get dict with data from tables
        data = self.GenerateValues()

        datarow = []
        add_data = ''

        # All data from dict append in list
        for i in range(self.rows_count):
            temp = []
            for value in data.values():
                temp.append(value[i])
            datarow.append(temp)

        # This madness need to format data in VALUES()
        for row in datarow:
            for item in row:
                if isinstance(item, str):
                    add_data += f"'{item}', "
                else:
                    add_data += str(item) + ', '

            add_data = add_data.rstrip(', ')
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
        indexes = []
        for index in self.indexes:
            indexes.append(self.CreateIndex(index))
        full_query += '\n'.join(indexes) + '\n\n'

        # Сборка значений
        full_query += self.queryrow1 + '\nVALUES '
        full_query += '      ,'.join(self.queryrow2)

        return full_query.rstrip('\n') + ';'
