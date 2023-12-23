import tkinter.messagebox as tkm
import sqlite3


class ErrorCatcher:
    """Класс предназначен для обработки пользовательских ошибок"""
    app_conn = sqlite3.Connection
    lang = str

    def __init__(self, lang_mode: str):
        self.app_conn = sqlite3.connect('app/app.db')
        self.lang = lang_mode

    def error_message(self, code, addon=''):
        """Возврашает сообщение об ошибке по коду"""
        cursor = self.app_conn.cursor()
        err_message = cursor.execute(f"SELECT lt.text, lt2.text "
                                     f"FROM t_err_codes ec,"
                                     f"     t_lang_text lt,"
                                     f"     t_lang_text lt2 "
                                     f"WHERE ec.err_code = '{code}' "
                                     f"AND   lt.lang = '{self.lang}' "
                                     f"AND   lt2.lang = '{self.lang}' "
                                     f"AND   ec.title = lt.label "
                                     f"AND   ec.message = lt2.label").fetchone()
        if err_message is None:
            tkm.showerror('Error', 'Необработанная ошибка!')
            return "UnhandledError"
        else:
            message = code + ': ' + err_message[1]
            if addon != '':
                message += '\n' + addon
            tkm.showerror(err_message[0], message)
            return err_message[1]
