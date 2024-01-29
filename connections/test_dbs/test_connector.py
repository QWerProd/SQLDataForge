from datetime import datetime


class TestConnector:

    conn_data = dict
    connector_name = str
    connection = None

    is_transaction = bool
    executed_queries = int
    rolling_queries = int
    time_transaction_opened = datetime

    class UnavaliableDatabaseError(Exception):
        def __init__(self, database_type):
            self.message = database_type

        def __str__(self):
            return 'the database type {0} is not avaliable'.format(self.message)

    def commit(self):
        try:
            if self.connector_name == 'SQLite':
                self.connection.commit()

            self.is_transaction = False
            executed = self.executed_queries
            transaction_time = datetime.now() - self.time_transaction_opened
            self.executed_queries = 0
            self.rolling_queries = 0
            self.time_transaction_opened = None
            return True, executed, transaction_time.total_seconds()
        except BaseException as e:
            return False, e.args[0]

    def rollback(self):
        try:
            if self.connector_name == 'SQLite':
                self.connection.rollback()

            self.is_transaction = False
            rolledback = self.rolling_queries
            transaction_time = datetime.now() - self.time_transaction_opened
            self.executed_queries = 0
            self.rolling_queries = 0
            self.time_transaction_opened = None
            return True, rolledback, transaction_time.total_seconds()
        except BaseException as e:
            return False, e.args[0]

    def close(self):
        if self.connector_name == 'SQLite':
            self.connection.close()

    def check_connection(self) -> bool:
        try:
            if self.connector_name == 'SQLite':
                curs = self.connection.cursor()
                curs.close()
            return True
        except BaseException as e:
            return False, e.args[0]

    def execute_query(self, query_str: str) -> int:
        query_pool = query_str.split('/')
        for query in query_pool:
            query = query.lstrip('\n')
            self.executed_queries += 1
            if query.startswith('INSERT'):
                self.rolling_queries += 1
        try:
            if self.connector_name == 'SQLite':
                curs = self.connection.cursor()
                for query in query_pool:
                    curs.execute(query)
                curs.close()
                if not self.is_transaction:
                    self.time_transaction_opened = datetime.now()

                    self.is_transaction = True
                return len(query_pool), None
        except BaseException as e:
            return -1, e.args[0]

    def get_conn_name(self) -> str: return self.connector_name

    def get_db_name(self) -> str: return self.conn_data['db-name']

    def __init__(self, conn_data: dict):
        self.conn_data = conn_data
        self.connector_name = self.conn_data['connector-name']
        self.is_transaction = False
        self.executed_queries = 0
        self.rolling_queries = 0
        self.time_transaction_opened = None

        if self.connector_name == 'SQLite':
            import sqlite3
            self.connection = sqlite3.connect(self.conn_data['db-path'])
        else:
            raise TestConnector.UnavaliableDatabaseError(self.connector_name)
