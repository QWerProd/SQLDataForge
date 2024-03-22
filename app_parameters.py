import sqlite3
import sys
import os
import wx

from app.error_catcher import ErrorCatcher


# Проверяем приложение на способ запуска (скрипт или exe)
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = sys._MEIPASS
elif __file__:
    APPLICATION_PATH = os.path.dirname(__file__)

catcher = ErrorCatcher('en')
app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))

APP_PARAMETERS = {
    'IS_CATCH_CLOSING_APP': str,
    'STC_COLOUR_WORD': str,
    'STC_COLOUR_COMMENT': str,
    'STC_COLOUR_NUMBER': str,
    'STC_COLOUR_STRING': str,
    'STC_FONT_SIZE': str,
    'STC_FONT_BOLD': str,
    'KEY_EXECUTE': str,
    'KEY_CLEAR_ALL': str,
    'KEY_REFRESH': str,
    'KEY_NEW_INSTANCE': str,
    'KEY_SAVE_SQL': str,
    'KEY_SETTINGS': str,
    'KEY_CREATE_UDB_WIZARD': str,
    'KEY_UDB_VIEWER': str,
    'FORMAT_DATE': str,
    'APP_LANGUAGE': str,
    'KEY_RECOVERY': str,
    'KEY_LOGVIEWER': str,
    'KEY_SAVE_AS': str,
    'SQL_KEYWORDS': "insert into values create table as primary key not null where and or like"
                    " if exists index on is unique update set ",
    'IS_ALIAS_UDB_USING': str,
    'KEY_NEW_TEST_CONN': str,
    'KEY_COMMIT': str,
    'KEY_ROLLBACK': str,
    'KEY_EXECUTE_SQL': str,
    'IS_CLOSING_REPORTS_AFTER_GEN': str,
    'DEFAULT_CONNECTOR': str,
    'SQL_TYPES_KEYWORDS': "text character char varchar integer int bigint numeric real float decimal"
                          " double date timestamp bool",
    'STC_COLOUR_TYPES': str
}

APP_LOCALES = {
    'ru': wx.LANGUAGE_RUSSIAN,
    'en': wx.LANGUAGE_ENGLISH
}

APP_TEXT_LABELS = dict()

# Установка параметров
curs = app_conn.cursor()

for param in APP_PARAMETERS.keys():
    try:
        param_name = curs.execute(f"SELECT param_value FROM t_params WHERE param_name = '{param}';").fetchone()
        APP_PARAMETERS[param] = param_name[0]
    except sqlite3.OperationalError as e:
        #catcher.error_message('E014', 'sqlite_errorname: ' + e.sqlite_errorname)
        exit(14)
    except TypeError:
        pass

# Установка словаря с текстом для labels
try:
    text_labels = curs.execute(f"""SELECT label, text
                                   FROM t_lang_text
                                   WHERE lang = '{APP_PARAMETERS['APP_LANGUAGE']}';""").fetchall()
    for text_row in text_labels:
        APP_TEXT_LABELS[text_row[0]] = text_row[1]
except sqlite3.Error as e:
    catcher.error_message('E014', 'sqlite_errorname: ' + e.sqlite_errorname)
    exit(14)
finally:
    curs.close()
    app_conn.close()
