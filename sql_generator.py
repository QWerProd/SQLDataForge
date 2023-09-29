import datetime

from data_controller import DataController as DC
import sqlite3
import random as rd
import pandas as pd


class SQLGenerator:
    app_conn = sqlite3.Connection
    queryrow1 = "INSERT INTO "
    queryrow2 = []
    table_name = ""
    new_table_info = {}
    rows_count = 0
    tables = []
    cols = []
    column_names = []

    def __init__(self, app_conn: sqlite3.Connection, table_info: dict, rows_count: int, tables: list) -> None:
        self.app_conn = app_conn
        for key, value in table_info.items():
            self.table_name = key
            self.new_table_info = value
        self.rows_count = rows_count
        self.queryrow2.clear()
        self.cols.clear()
        self.column_names.clear()
        self.tables = tables

    def CreateHeader(self):
        self.queryrow1 += self.table_name
        col_names = []
        if self.new_table_info['is_id_create']:
            col_names.append('id')
        for tables in self.tables:
            col_names.append(tables.split(':')[1])
        res = ', '.join(col_names)
        self.queryrow1 += '(' + res + ')'

    def CreateTable(self) -> str:
        query_createtable = f'CREATE TABLE {self.table_name}(\n    '
        items = []
        if self.new_table_info['is_id_create']:
            items.append(f'id INTEGER NOT NULL\n')
        for col in self.cols:
            items.append(f'{col[1]} {col[3]}\n')
        query_createtable += '   ,'.join(items)
        if self.new_table_info['is_id_create']:
            query_createtable += '    PRIMARY KEY("id")\n'
        query_createtable += ');'
        return query_createtable

    def GenerateValues(self) -> dict:
        list_of_dbs = DC.GetDBFromTables(self.tables)
        app_curs = self.app_conn.cursor()
        path_of_dbs = app_curs.execute('SELECT path FROM t_databases ' +
                                       'WHERE dbname IN ("' + '","'.join(list_of_dbs) + '")').fetchone()
        databases = []
        for i in range(0, len(list_of_dbs)):
            databases.append((list_of_dbs[i], path_of_dbs[i]))

        datadict = dict()

        id_column = False
        if self.new_table_info['is_id_create']:
            increment = int(self.new_table_info['increment_start'])
            id_column = True
            if id_column:
                row = []
                for i in range(increment, self.rows_count + increment):
                    row.append(i)
                datadict['id'] = row
                self.column_names.append('id')

        for database in databases:
            conn = sqlite3.connect(database[1])
            cursor = conn.cursor()
            temp_cols = []

            for colnames in self.tables:
                temp_cols.append([colnames.split(':')[0], colnames.split(':')[1]])

            for item in temp_cols:
                query = f"""SELECT table_name, column_name, gen_key, column_type
                        FROM t_cases_info
                        WHERE table_name = "{item[0]}"
                        AND   column_name = "{item[1]}";"""
                temp_cols = cursor.execute(query).fetchone()
                self.cols.append(temp_cols)

            # Generate data from all tables
            for table in self.cols:
                # Getting maximum value of rows
                max_val = cursor.execute(f"SELECT COUNT(*) FROM {table[0]};").fetchone()[0]

                # Creating list of columns
                self.column_names.append(table[1])

                datadict[table[1]] = list()

                for i in range(self.rows_count):
                    # Getting random data from datasets
                    if table[2] == 'RSet':
                        row_number = rd.randint(1, max_val)
                        data = cursor.execute(f"""SELECT {table[1]}
                                                  FROM {table[0]}
                                                  WHERE id = {row_number};""").fetchone()[0]
                        datadict[table[1]].append(data)
                    # Generating random number in given interval
                    elif table[2] == 'RValue':
                        break
                        # Временно не поддерживается!
                        # dirty_values = cursor.execute(f"""SELECT minvalue, maxvalue
                        #                                   FROM {table[0]};""").fetchone()
                        # minvalue = int(dirty_values[0])
                        # maxvalue = int(dirty_values[1])
                        #
                        # datadict[table[0]].append((rd.randint(minvalue, maxvalue), ))
                    elif table[2] == 'RDate':
                        data = cursor.execute(f"""SELECT minvalue, minvalue_subtract, maxvalue, maxvalue_subtract
                                                  FROM {table[0]};""").fetchone()
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
                        datadict[table[1]].append(str(mindate + datetime.timedelta(days=rnd_day)))
            cursor.close()
            conn.close()

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

    def BuildQuery(self, isTable = False) -> str:
        full_query = ''
        self.CreateBody()
        self.CreateHeader()
        if isTable:
            full_query += self.CreateTable() + '\n\n'
        full_query += self.queryrow1 + '\nVALUES '
        full_query += '      ,'.join(self.queryrow2)

        return full_query.rstrip('\n') + ';'
