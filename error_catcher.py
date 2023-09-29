import wx
from tkinter import messagebox
import sqlite3


class ErrorCatcher:
    """Класс предназначен для обработки пользовательских ошибок"""
    app_conn = None

    def __init__(self):
        self.app_conn = sqlite3.connect('app/app.db')

    def error_message(self, code):
        """Возврашает сообщение об ошибке по коду"""
        cursor = self.app_conn.cursor()
        err_message = cursor.execute(f"SELECT title, message FROM t_err_codes WHERE err_code = '{code}'").fetchone()
        if err_message is None:
            messagebox.showerror("Необработанная ошибка", "Error")
            return "Error"
        else:
            messagebox.showerror(err_message[0], code + ': ' + err_message[1])
            return err_message[1]
