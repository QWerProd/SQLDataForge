import re
import os
import sqlite3
import psycopg2
import mysql.connector
from sshtunnel import SSHTunnelForwarder, HandlerSSHTunnelForwarderError
from datetime import datetime


##################################################
# EXCEPTIONS
##################################################

class DestroyedConnectionError(BaseException):
    
    def __init__(self, path: str, conn: str, addition_info: str = ''):
        """The exception thrown out with an unexpected disconnection from the database
            (while checking the connection)

            Args:
                path (str): the path to database (key 'database-path' from test_conns.json)
                conn (str): connector type
                addition_info (str, optional): information from trowned exception to display in ErrorCatcher 
        """

        self.path_to_db = path
        self.type_connector = conn
        self.addition_info = addition_info

    def __str__(self): return 'connection to {0}:///{1} is destroyed'.format(self.type_connector, self.path_to_db)


class DestroyedSSHTunnelError(BaseException):
   
    def __init__(self, path: str, addition_info: str = ''): 
        """The exception thrown out with an unexpected disconnecting from the SSH tunnel (with sshtunnel.HandlerSSHTunnelForwarderError)
            (while checking the connection) 

            Args:
                path (str): SSH path (key 'ssh-path' from test_conns.json)
                addition_info (str, optional): information from trowned exception to display in ErrorCatcher
        """
        self.path_ssh = path
        self.addition_info = addition_info

    def __str__(self): return 'SSH tunnel to {0} is destroyed'.format(self.path_ssh)


class SetConnectionError(BaseException):

    def __init__(self, path: str, conn: str, addition_info: str = ''): 
        """The exception thrown out when an error of connection to the database along the specified path

            Args:
                path (str): the path to database (key 'database-path' from test_conns.json)
                conn (str): connector type
                addition_info (str, optional): information from trowned exception to display in ErrorCatcher
        """
        self.path_to_db = path
        self.type_connector = conn
        self.addition_info = addition_info

    def __str__(self): return 'set connection to {0}:///{1} is not possible'.format(self.type_connector, self.path_to_db)


class SetSSHTunnelError(BaseException):

    def __init__(self, path: str, addition_info: str = ''):
        """The exception is thrown out if it is impossible to open the SSH tunnel (with sshtunnel.HandlerSSHTunnelForwarderError)

        Args:
            path (str): SSH path (key 'ssh-path' from test_conns.json)
            addition_info (str, optional): information from trowned exception to display in ErrorCatcher
        """
        self.ssh_path = path
        self.addition_path = addition_info

    def __str__(self): return 'set connection to SSH tunnel {0} is not possible'.format(self.ssh_path)


class OperationalSQLError(BaseException):

    def __init__(self, path: str, conn: str, addition_info: str = ''):
        """The exception is released when an error occurs when working with requests and transactions
        
            Args:
                path (str): the path to database (key 'database-path' from test_conns.json)
                conn (str): connector type
                addition_info (str, optional): information from trowned exception to display in ErrorCatcher
        """
        self.path_to_db = path
        self.type_connector = conn
        self.addition_info = addition_info 

    def __str__(self): return 'error when trying to make a request in {0}:///{1}'.format(self.type_connector, self.path_to_db)


##################################################
# CONNECTORS
##################################################

class BaseConnector:

    connection = None
    connector_info = dict

    is_transaction = bool
    executed_queries = int
    rolling_queries = int
    time_transaction_opened = datetime

    def get_conn_name(self) -> str: return self.connector_info['connector-name']

    def get_db_name(self) -> str: return self.connector_info['database-name']

    def commit(self):
        """Changing statuses after the commit and receiving the time opening the transaction (how long it lasted)"""
        self.is_transaction = False
        executed = self.executed_queries
        transaction_time = datetime.now() - self.time_transaction_opened
        self.executed_queries = 0
        self.rolling_queries = 0
        self.time_transaction_opened = None
        return executed, transaction_time.total_seconds()

    def rollback(self):
        """Changing statuses after the rollback and receiving the time opening the transaction (how long it lasted)"""
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
        """Checking the connection with the open connection"""
        pass

    def init_execute_query(self, query: str) -> list:
        """Opening a transaction and breaking input script string into an array of requests"""
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
        """Selfdestroy connection and object"""
        del self

    def __init__(self, connector_info: dict):
        """Initialization of state variables
        
        Args:
            connector_info (dict): information about connector and connection
        """

        self.connector_info = connector_info
        self.is_transaction = False
        self.executed_queries = 0
        self.rolling_queries = 0
        self.time_transaction_opened = None


class SQLiteConnector(BaseConnector):

    db_path = str

    def commit(self):
        if self.check_connection():
            try:
                self.connection.commit()
                executed, transaction_time = super().commit()

                return True, executed, transaction_time
            except sqlite3.Error as e:
                raise OperationalSQLError(self.db_path, 'sqlite', addition_info=str(e))

    def rollback(self):
        if self.check_connection():
            try:
                self.connection.rollback()
                rolledback, transaction_time = super().rollback()

                return True, rolledback, transaction_time
            except sqlite3.Error as e:
                raise OperationalSQLError(self.db_path, 'sqlite', addition_info=str(e))

    @staticmethod
    def test_connection(db_path: str, db_user_info: str = None, ssh_path: str = None, ssh_user_info: str = None) -> bool:
        try:
            # Проверяем наличие файла БД
            if not os.path.exists(db_path):
                raise SetConnectionError(db_path, 'sqlite', addition_info='DB file is not exists on {0}'.format(db_path))

            # Открываем подключение
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.close()
            conn.close()
            return True
        except sqlite3.Error as e:
            raise SetConnectionError(db_path, 'sqlite', addition_info=str(e))

    def check_connection(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.close()
            return True
        except sqlite3.Error as e:
            self.close()

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
            except sqlite3.OperationalError as e:
                raise OperationalSQLError(self.db_path, 'sqlite', addition_info=str(e))

    def close(self):
        try:
            self.connection.close()
            super().close()
        except sqlite3.Error as e:
            raise DestroyedConnectionError(self.db_path, 'sqlite', addition_info=str(e))

    def __init__(self, connector_info: dict):
        BaseConnector.__init__(self, connector_info)
        try:
            # Проверка наличия файла БД
            if not os.path.exists(connector_info['database-path']):
                raise SetConnectionError(connector_info['database-path'], 'sqlite', 
                                         addition_info='DB file is not exists on {0}'.format(connector_info['database-path']))

            self.connection = sqlite3.connect(self.connector_info['database-path'])
            self.db_path = connector_info['database-path']
        except sqlite3.Error:
            self.close()


class PostgreSQLConnector(BaseConnector):

    server = SSHTunnelForwarder
    db_path = str
    ssh_path = str

    def commit(self):
        if self.check_connection():
            try:
                self.connection.commit()
                executed, transaction_time = super().commit()

                return True, executed, transaction_time
            except psycopg2.OperationalError as e:
                raise OperationalSQLError(self.db_path, 'postgres', addition_info=str(e))

    def rollback(self):
        if self.check_connection():
            try:
                self.connection.rollback()
                rolledback, transaction_time = super().rollback()

                return True, rolledback, transaction_time
            except psycopg2.OperationalError as e:
                return OperationalSQLError(self.db_path, 'postgres', addition_info=str(e))

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
        except psycopg2.Error as e:
            raise SetConnectionError(db_path, 'postgres', addition_info=str(e))
        except HandlerSSHTunnelForwarderError as e:
            raise SetSSHTunnelError(ssh_path, addition_info=str(e))

    def check_connection(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.close()
            return True
        except (HandlerSSHTunnelForwarderError, psycopg2.Error):
            self.close()

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
                return len(query_pool)
            except HandlerSSHTunnelForwarderError as e:
                raise SetSSHTunnelError(self.ssh_path, addition_info=str(e))
            except psycopg2.Error as e:
                raise SetConnectionError(self.db_path, 'postgres', addition_info=str(e))

    def close(self):
        try:
            self.connection.close()
            if self.connector_info['ssh']:
                self.server.stop()
            super().close()
        except HandlerSSHTunnelForwarderError as e:
            raise DestroyedSSHTunnelError(self.ssh_path, addition_info=str(e))
        except psycopg2.Error as e:
            raise DestroyedConnectionError(self.db_path, 'postgres', addition_info=str(e))

    def __init__(self, connector_info: dict):
        BaseConnector.__init__(self, connector_info)
        self.db_path = connector_info['database-path']
        db_host, db_port, database = re.split(r'[\:\/]', connector_info['database-path'])
        if connector_info['ssh']:
            self.ssh_path = connector_info['ssh-path']
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
                raise SetSSHTunnelError(self.ssh_path, addition_info=str(e))
            except psycopg2.OperationalError as e:
                raise SetConnectionError(self.db_path, 'postgres', addition_info=str(e))
        else:
            try:
                self.connection = psycopg2.connect(user=connector_info['database-username'],
                                                   password=connector_info['database-password'],
                                                   host=db_host,
                                                   port=db_port,
                                                   database=database)
            except psycopg2.Error:
                raise SetConnectionError(self.db_path, 'postgres', addition_info=str(e))


class MySQLConnector(BaseConnector):

    server = SSHTunnelForwarder
    db_path = str
    ssh_path = str

    def commit(self):
        if self.check_connection():
            try:
                self.connection.commit()
                executed, transaction_time = super().commit()

                return True, executed, transaction_time
            except mysql.connector.OperationalError as e:
                raise OperationalSQLError(self.db_path, 'mysql', addition_info=str(e))

    def rollback(self):
        if self.check_connection():
            try:
                self.connection.rollback()
                rolledback, transaction_time = super().rollback()

                return True, rolledback, transaction_time
            except mysql.connector.OperationalError:
                raise OperationalSQLError(self.db_path, 'mysql', addition_info=str(e))

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
        except mysql.connector.Error as e:
            raise SetConnectionError(db_path, 'mysql', addition_info=str(e))
        except HandlerSSHTunnelForwarderError as e:
            raise SetSSHTunnelError(ssh_path, addition_info=str(e))

    def check_connection(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.close()
            return True
        except (HandlerSSHTunnelForwarderError, mysql.connector.Error) as e:
            self.close()

    def execute_query(self, query_str: str) -> int:
        if self.check_connection():
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
            except mysql.connector.OperationalError as e:
                raise OperationalSQLError(self.db_path, 'mysql', addition_info=str(e))

    def close(self):
        try:
            self.connection.close()
            if self.connector_info['ssh']:
                self.server.stop()
            super().close()
        except HandlerSSHTunnelForwarderError as e:
            raise SetSSHTunnelError(self.ssh_path, addition_info=str(e))
        except mysql.connector.Error as e:
            raise SetConnectionError(self.db_path, 'mysql', addition_info=str(e))

    def __init__(self, connector_info: dict):
        BaseConnector.__init__(self, connector_info)
        db_host, db_port, database = re.split(r'[\:\/]', connector_info['database-path'])
        self.db_path = connector_info['database-path']
        if connector_info['ssh']:
            ssh_host, ssh_port = connector_info['ssh-path'].split(':')
            self.ssh_path = connector_info['ssh-path']
            try:
                self.server = SSHTunnelForwarder((ssh_host, int(ssh_port)),
                                                 ssh_password=connector_info['ssh-pass'],
                                                 ssh_username=connector_info['ssh-user'],
                                                 remote_bind_address=(db_host, int(db_port)))
                self.server.start()
                self.connection = mysql.connector.connect(database=database, port=self.server.local_bind_port,
                                                          user=connector_info['database-username'], password=connector_info['database-password'])
            except HandlerSSHTunnelForwarderError as e:
                raise SetSSHTunnelError(self.ssh_path, addition_info=str(e))
            except mysql.connector.Error as e:
                raise SetConnectionError(self.db_path, 'mysql', addition_info=str(e))
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