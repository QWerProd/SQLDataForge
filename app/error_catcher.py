import datetime
import tkinter.messagebox as tkm
import sqlite3
import os
import sys


class ErrorCatcher:
    """Класс предназначен для обработки пользовательских ошибок"""
    lang = str
    db_path = str

    def __init__(self, lang_mode: str):
        self.lang = lang_mode
        if getattr(sys, 'frozen', False):
            BASE_DIR = os.path.join(sys._MEIPASS, 'app\\')
        elif __file__:
            BASE_DIR = os.path.dirname(__file__)
        self.db_path = os.path.join(BASE_DIR, 'app.db')

        # Создание таблицы логов if not exists
        with sqlite3.connect(self.db_path) as app_conn:
            curs = app_conn.cursor()
            curs.execute('CREATE TABLE IF NOT EXISTS "t_error_log" ('
                         '"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, '
                         '"error_code"	TEXT NOT NULL, '
                         '"date_catched"	TEXT NOT NULL);')
            app_conn.commit()

    def error_message(self, code, addon=''):
        """Возврашает сообщение об ошибке по коду"""
        app_conn = sqlite3.connect(self.db_path)
        cursor = app_conn.cursor()
        err_message = cursor.execute(f"SELECT lt.text, lt2.text "
                                     f"FROM t_err_codes ec,"
                                     f"     t_lang_text lt,"
                                     f"     t_lang_text lt2 "
                                     f"WHERE ec.err_code = '{code}' "
                                     f"AND   lt.lang = '{self.lang}' "
                                     f"AND   lt2.lang = '{self.lang}' "
                                     f"AND   ec.title = lt.label "
                                     f"AND   ec.message = lt2.label").fetchone()
        cursor.close()
        app_conn.close()

        if err_message is None:
            tkm.showerror('Error', 'Unhangled error!')
            self.put_log("E-1")
            return "E-1"
        else:
            message = code + ': ' + err_message[1]
            if addon != '':
                message += '\n' + addon
            tkm.showerror(err_message[0], message)
            self.put_log(code)
            return code

    def put_log(self, code):
        with sqlite3.connect(self.db_path) as app_conn:
            cursor = app_conn.cursor()
            cursor.execute(f"""INSERT INTO t_error_log(error_code, date_catched)
                               VALUES ('{code}', '{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')}');""")
            app_conn.commit()
            cursor.close()
