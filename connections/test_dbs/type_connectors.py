import re
import sqlite3
import psycopg2
import mysql.connector
from sshtunnel import SSHTunnelForwarder, HandlerSSHTunnelForwarderError
from datetime import datetime
from app.error_catcher import ErrorCatcher
from app_parameters import APP_PARAMETERS

catcher = ErrorCatcher(APP_PARAMETERS['APP_LANGUAGE'])


class DestroyedConnectionError(BaseException):
    def __init__(self): pass

    def __str__(self): return 'connection was been destroyed'


class DestroyedTunnelError(BaseException):
    def __init__(self): pass

    def __str__(self): return 'tunnel SSH was been destroyed'


class BaseConnector:

    connection = None
    connector_info = dict

    is_transaction = bool
    executed_queries = int
    rolling_queries = int
    time_transaction_opened = datetime

    def get_conn_name(self) -> str: return self.connector_info['connector-name']

    def get_db_name(self) -> str: return self.connector_info['database-name']

    def commit(self) -> (int, float):
        """Изменение статусов после коммита и получение времени открытия транзакции (сколько длилась)"""
        self.is_transaction = False
        executed = self.executed_queries
        transaction_time = datetime.now() - self.time_transaction_opened
        self.executed_queries = 0
        self.rolling_queries = 0
        self.time_transaction_opened = None
        return executed, transaction_time.total_seconds()

    def rollback(self) -> (int, float):
        """Изменение статусов после отката транзации и получение времени открытия транзакции (сколько длилась)"""
        self.is_transaction = False
        rolledback = self.rolling_queries
        transaction_time = datetime.now() - self.time_transaction_opened
        self.executed_queries = 0
        self.rolling_queries = 0
        self.time_transaction_opened = None
        return rolledback, transaction_time.total_seconds()

    @staticmethod
    def test_connection(db_path: str, db_user_info: str = None, ssh_path: str = None, ssh_user_info: str = None) -> bool:
        pass

    def check_connection(self) -> bool:
        """Проверка подключения при открытом соединении"""
        pass

    def init_execute_query(self, query: str) -> list:
        """Открытие транзакции и разбитие строки запроса на массив запросов"""
        query_pool = list
        try:
            query_pool = query.split('/')
        except BaseException:
            query_pool = []

        if not self.is_transaction and len(query_pool) > 0:
            self.is_transaction = True
            self.time_transaction_opened = datetime.now()
        return query_pool

    def close(self):
        """Самоуничтожение"""
        del self

    def __init__(self, connector_info: dict):
        """Инициализация переменных состояния"""
        self.connector_info = connector_info
        self.is_transaction = False
        self.executed_queries = 0
        self.rolling_queries = 0
        self.time_transaction_opened = None


class SQLiteConnector(BaseConnector):

    def commit(self):
        try:
            self.connection.commit()
            executed, transaction_time = super().commit()

            return True, executed, transaction_time
        except sqlite3.Error as e:
            return False, str(e)

    def rollback(self):
        try:
            self.connection.rollback()
            rolledback, transaction_time = super().rollback()

            return True, rolledback, transaction_time
        except sqlite3.Error as e:
            return False, str(e)

    @staticmethod
    def test_connection(db_path: str, db_user_info: str = None, ssh_path: str = None, ssh_user_info: str = None) -> bool:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.close()
            conn.close()
            return True
        except BaseException:
            return False

    def check_connection(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.close()
            return True
        except sqlite3.Error:
            return False

    def execute_query(self, query_str: str) -> int:
        query_pool = super().init_execute_query(query_str)
        if self.check_connection():
            try:
                curs = self.connection.cursor()
                for query in query_pool:
                    query = query.lstrip('\n')
                    curs.execute(query)
                    self.executed_queries += 1
                    if query.startswith('INSERT'):
                        self.rolling_queries += 1
                curs.close()
                return len(query_pool), None
            except sqlite3.Error as e:
                return -1, e.args[0]
        else:
            self.close()

    def close(self):
        try:
            self.connection.close()
            super().close()
        except:
            raise DestroyedConnectionError

    def __init__(self, connector_info: dict):
        BaseConnector.__init__(self, connector_info)
        try:
            self.connection = sqlite3.connect(self.connector_info['database-path'])
        except sqlite3.Error:
            self.close()


class PostgreSQLConnector(BaseConnector):

    server = SSHTunnelForwarder

    def commit(self) -> (int, float):
        try:
            self.connection.commit()
            executed, transaction_time = super().commit()

            return True, executed, transaction_time
        except psycopg2.Error:
            return False, str(e)

    def rollback(self) -> (int, float):
        try:
            self.connection.rollback()
            rolledback, transaction_time = super().rollback()

            return True, rolledback, transaction_time
        except psycopg2.Error:
            return False, str(e)

    @staticmethod
    def test_connection(db_path: str, db_user_info: str, ssh_path: str = None, ssh_user_info: str = None) -> bool:
        db_host, db_port, db_name = re.split(r'[\:\/]', db_path)
        db_user, db_pass = db_user_info.split(':')
        try:
            if ssh_path is None:
                conn = psycopg2.connect(user=db_user,
                                        password=db_pass,
                                        host=db_host,
                                        port=db_port,
                                        database=db_name)
                curs = conn.cursor()
                curs.close()
                conn.close()
            else:
                ssh_host, ssh_port = ssh_path.split(':')
                ssh_user, ssh_pass = ssh_user_info.split(':')
                server = SSHTunnelForwarder((ssh_host, int(ssh_port)),
                                            ssh_username=ssh_user,
                                            ssh_password=ssh_pass,
                                            remote_bind_address=(db_host, int(db_port)))
                server.start()
                conn = psycopg2.connect(database=db_name, port=server.local_bind_port,
                                        user=db_user, password=db_pass)
                curs = conn.cursor()
                curs.close()
                conn.close()
                server.stop()

            return True
        except HandlerSSHTunnelForwarderError as e:
            catcher.error_message('E022', str(e))
            return False
        except psycopg2.Error as e:
            catcher.error_message('E021', str(e))
            return False

    def check_connection(self) -> bool:
        try:
            self.connection.cursor().close()
            return True
        except HandlerSSHTunnelForwarderError as e:
            catcher.error_message('E022', str(e))
            return False
        except psycopg2.Error as e:
            catcher.error_message('E021', str(e))
            return False

    def execute_query(self, query_str: str) -> int:
        query_pool = super().init_execute_query(query_str)
        try:
            curs = self.connection.cursor()
            for query in query_pool:
                query = query.lstrip('\n')
                curs.execute(query)
                self.executed_queries += 1
                if query.startswith('INSERT'):
                    self.rolling_queries += 1
            curs.close()
            return len(query_pool), None
        except HandlerSSHTunnelForwarderError as e:
            catcher.error_message('E022', str(e))
            return -1, None
        except psycopg2.Error as e:
            catcher.error_message('E021', str(e))
            return -1, None

    def close(self):
        try:
            self.connection.close()
            if self.connector_info['ssh']:
                self.server.stop()
            super().close()
        except:
            raise DestroyedConnectionError

    def __init__(self, connector_info: dict):
        BaseConnector.__init__(self, connector_info)
        db_host, db_port, database = re.split(r'[\:\/]', connector_info['database-path'])
        if connector_info['ssh']:
            ssh_host, ssh_port = connector_info['ssh-path'].split(':')
            try:
                self.server = SSHTunnelForwarder((ssh_host, int(ssh_port)),
                                                 ssh_password=connector_info['ssh-pass'],
                                                 ssh_username=connector_info['ssh-user'],
                                                 remote_bind_address=(db_host, int(db_port)))
                self.server.start()
                self.connection = psycopg2.connect(database=database, port=self.server.local_bind_port,
                								   user=connector_info['database-username'], password=connector_info['database-password'])
            except HandlerSSHTunnelForwarderError as e:
                catcher.error_message('E022', str(e))
                raise DestroyedTunnelError
            except psycopg2.OperationalError as e:
            	catcher.error_message('E021', str(e))
            	raise DestroyedConnectionError

        else:
            try:
                self.connection = psycopg2.connect(user=connector_info['database-username'],
                                                   password=connector_info['database-password'],
                                                   host=db_host,
                                                   port=db_port,
                                                   database=database)
            except psycopg2.Error:
                catcher.error_message('E021', e.args[0])
                raise DestroyedConnectionError


class MySQLConnector(BaseConnector):

    server = SSHTunnelForwarder

    def commit(self) -> (int, float):
        try:
            self.connection.commit()
            executed, transaction_time = super().commit()

            return True, executed, transaction_time
        except mysql.connector.Error:
            return False, str(e)

    def rollback(self) -> (int, float):
        try:
            self.connection.rollback()
            rolledback, transaction_time = super().rollback()

            return True, rolledback, transaction_time
        except mysql.connector.Error:
            return False, str(e)

    @staticmethod
    def test_connection(db_path: str, db_user_info: str, ssh_path: str = None, ssh_user_info: str = None) -> bool:
        db_host, db_port, db_name = re.split(r'[\:\/]', db_path)
        db_user, db_pass = db_user_info.split(':')
        try:
            if ssh_path == '':
                connection = mysql.connector.connect(user=db_user,
                                        password=db_pass,
                                        host=db_host,
                                        port=db_port,
                                        database=db_name)
                cursor = connection.cursor()
                cursor.close()
                connection.close()
            else:
                ssh_host, ssh_port = ssh_path.split(':')
                ssh_user, ssh_pass = ssh_user_info.split(':')
                server = SSHTunnelForwarder((ssh_host, ssh_port),
                                            ssh_username=ssh_user,
                                            ssh_password=ssh_pass,
                                            remote_bind_address=(db_host, db_port))
                server.start()
                connection = mysql.connector.connect(database=db_name, port=server.local_bind_port)
                cursor = connection.cursor()
                cursor.close()
                connection.close()
                server.stop()
            return True
        except HandlerSSHTunnelForwarderError as e:
            catcher.error_message('E022', str(e))
            return False
        except mysql.connector.Error as e:
            catcher.error_message('E021', str(e))
            return False

    def check_connection(self) -> bool:
        try:
            self.connection.cursor().close()
            return True
        except HandlerSSHTunnelForwarderError as e:
            catcher.error_message('E022', str(e))
            return False
        except mysql.connector.Error as e:
            catcher.error_message('E021', str(e))
            return False

    def execute_query(self, query_str: str) -> int:
        query_pool = super().init_execute_query(query_str)
        try:
            curs = self.connection.cursor()
            for query in query_pool:
                query = query.lstrip('\n')
                curs.execute(query)
                self.executed_queries += 1
                if query.startswith('INSERT'):
                    self.rolling_queries += 1
            curs.close()
            return len(query_pool), None
        except HandlerSSHTunnelForwarderError as e:
            catcher.error_message('E022', str(e))
            return -1, None
        except mysql.connector.Error as e:
            catcher.error_message('E021', str(e))
            return -1, None

    def close(self):
        try:
            self.connection.close()
            if self.connector_info['ssh']:
                self.server.stop()
            super().close()
        except:
            raise DestroyedConnectionError

    def __init__(self, connector_info: dict):
        BaseConnector.__init__(self, connector_info)
        db_host, db_port, database = re.split(r'[\:\/]', connector_info['database-path'])
        if connector_info['ssh']:
            ssh_host, ssh_port = connector_info['ssh-path'].split(':')
            try:
                self.server = SSHTunnelForwarder((ssh_host, int(ssh_port)),
                                                 ssh_password=connector_info['ssh-pass'],
                                                 ssh_username=connector_info['ssh-user'],
                                                 remote_bind_address=(db_host, int(db_port)))
                self.server.start()
                self.connection = mysql.connector.connect(database=database, port=self.server.local_bind_port,
                                                          user=connector_info['database-username'], password=connector_info['database-password'])
            except HandlerSSHTunnelForwarderError as e:
                catcher.error_message('E022', str(e))
            except mysql.connector.Error as e:
                catcher.error_message('E021', str(e))
        else:
            try:
                self.connection = mysql.connector.connect(user=connector_info['database-username'],
                                                          password=connector_info['database-password'],
                                                          host=db_host,
                                                          port=db_port,
                                                          database=database)
            except mysql.connector.Error as e:
                catcher.error_message('E021', str(e))
                raise DestroyedConnectionError

# Доступные типы коннекторов
avaliable_connectors = {
    'SQLite': SQLiteConnector,
    'PostgreSQL': PostgreSQLConnector,
    'MySQL': MySQLConnector
}