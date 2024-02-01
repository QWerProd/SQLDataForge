import wx
import os
import sys
import sqlite3
from threading import Thread
from pubsub import pub

APP_TEXT_LABELS = {
    'RECOVERY.ACTIONS': 'Resetting the system DB',
    'MAIN.STATUSBAR.STATUS.DONE': 'Done',
    'RECOVERY.HEADER': 'Recovery',
    'RECOVERY.HEADER2': 'Recovery mode',
    'RECOVERY.CHOOSE_ACTION': 'Choose action:',
    'BUTTON.CANCEL': 'Cancel',
    'BUTTON.DO': 'GO'
}

if getattr(sys, 'frozen', False):
    RECOVERY_PATH = sys._MEIPASS
elif __file__:
    RECOVERY_PATH = os.path.dirname(__file__)


class Recovery(wx.Frame):

    choices = list
    curr_action = int
    progressbar_value = int
    progressbar_max = int

    def change_action(self, event):
        self.curr_action = self.action_choice.GetSelection()
        self.action_button.Enable()

    def increment_progressbar(self, msg):
        self.progressbar_value += 1

        if self.progressbar.GetRange() < self.progressbar_value:
            print(self.progressbar_value)
            self.progressbar_value = self.progressbar.GetRange()

        self.progressbar.SetValue(self.progressbar_value)
        self.status_statictext.SetLabel(str(self.progressbar_value) + ' - ' + str(self.progressbar_max))

    @staticmethod
    def get_last_exit_code() -> str:
        app_conn = sqlite3.connect(os.path.join(RECOVERY_PATH, 'app/app.db'))
        curs = app_conn.cursor()
        try:
            err_code = curs.execute("""SELECT error_code FROM t_error_log WHERE date_catched = (SELECT MAX(date_catched) FROM t_error_log);""").fetchone()[0]
            return err_code
        except sqlite3.Error:
            return 'E014'    # Ошибка целостности сБД
        except TypeError:
            return ''
        finally:
            curs.close()
            app_conn.close()

    def recovery_sdb(self):
        scripts = list
        with open(os.path.join(RECOVERY_PATH, 'app/sql_scripts/sdb_dump.sql'), encoding='utf-8') as file:
            file_text = file.read()
            scripts = file_text.split('/')
        pub.sendMessage("recovery_sdb", msg="")

        app_conn = sqlite3.Connection
        cursor = sqlite3.Cursor
        try:
            try:
                os.remove(os.path.join(RECOVERY_PATH, 'app/app.db'))
            # except PermissionError:
            #     pass
            except FileNotFoundError:
                pass
            app_conn = sqlite3.connect(os.path.join(RECOVERY_PATH, 'app/app.db'))
            cursor = app_conn.cursor()
            for script in scripts:
                cursor.execute(script)
                app_conn.commit()
                pub.sendMessage("recovery_sdb", msg="")
                print(script)
            self.status_statictext.SetLabel(APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.DONE'])
        except sqlite3.Error as e:
            wx.MessageBox('The recovery script is corrupted!', 'Recovery error', wx.ICON_ERROR)
        finally:
            pub.unsubscribe(self.increment_progressbar, "recovery_sdb")

    def recovery_action(self, event: wx.Event = None):
        self.status_statictext.Show()
        self.progressbar.Show()
        self.main_panel.Layout()
        if self.curr_action == 0:
            pub.subscribe(self.increment_progressbar, "recovery_sdb")
            # Просмотр кол-ва запросов для progressbar
            with open(os.path.join(RECOVERY_PATH, 'app/sql_scripts/sdb_dump.sql'), encoding='utf-8') as file:
                file_text = file.read()
                sql_scripts = file_text.split('/')
                self.progressbar_max = len(sql_scripts)
                self.progressbar.SetRange(self.progressbar_max)
                self.status_statictext.SetLabel("0 - " + str(self.progressbar_max))
            recovery_thread = Thread(None, self.recovery_sdb)
            recovery_thread.run()

    def __init__(self, recovery_code: int = None):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['RECOVERY.HEADER'],
                          style=wx.CAPTION | wx.CLOSE_BOX, size=(500, 300))
        self.SetIcon(wx.Icon(os.path.join(RECOVERY_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.SetMinSize((500, 300))
        self.SetMaxSize((500, 300))
        self.choices = APP_TEXT_LABELS['RECOVERY.ACTIONS'].split(':')
        self.progressbar_value = 0
        if recovery_code is not None:
            self.curr_action = recovery_code
        else:
            self.curr_action = int

        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        self.small_header_font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)

        # ---------------

        header_panel = wx.Panel(self.main_panel)
        header_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_panel.SetSizer(header_sizer)

        header_image = wx.Image(os.path.join(RECOVERY_PATH, 'img/32x32/database.png'), wx.BITMAP_TYPE_PNG)
        header_bitmap = wx.StaticBitmap(header_panel, bitmap=wx.BitmapFromImage(header_image))
        header_sizer.Add(header_bitmap, 0, wx.ALL, 10)

        # ------------------------------

        header_info_panel = wx.Panel(header_panel)
        header_info_sizer = wx.BoxSizer(wx.VERTICAL)
        header_info_panel.SetSizer(header_info_sizer)

        info_header_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['RECOVERY.HEADER'])
        info_header_statictext.SetFont(self.small_header_font)
        header_info_sizer.Add(info_header_statictext, 0, wx.ALL)

        info_data_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['RECOVERY.HEADER2'])
        header_info_sizer.Add(info_data_statictext, 0, wx.ALL)

        header_sizer.Add(header_info_panel, 0, wx.ALL, 10)
        # ------------------------------

        self.main_sizer.Add(header_panel, 0, wx.EXPAND)
        self.main_sizer.Add(wx.StaticLine(self.main_panel), 0, wx.EXPAND)
        # ---------------

        self.action_panel = wx.Panel(self.main_panel)
        self.action_sizer = wx.BoxSizer(wx.VERTICAL)
        self.action_panel.SetSizer(self.action_sizer)

        choose_action_statictext = wx.StaticText(self.action_panel, label=APP_TEXT_LABELS['RECOVERY.CHOOSE_ACTION'])
        self.action_sizer.Add(choose_action_statictext, 0, wx.LEFT | wx.TOP, 20)

        self.action_choice = wx.Choice(self.action_panel, choices=self.choices,
                                       size=(150, -1))
        self.action_choice.Bind(wx.EVT_CHOICE, self.change_action)
        self.action_sizer.Add(self.action_choice, 0, wx.LEFT | wx.BOTTOM, 20)

        self.main_sizer.Add(self.action_panel, 1, wx.EXPAND)
        # ---------------

        self.status_statictext = wx.StaticText(self.main_panel)
        self.status_statictext.Hide()
        self.main_sizer.Add(self.status_statictext, 0, wx.LEFT, 5)
        self.progressbar = wx.Gauge(self.main_panel, style=wx.GA_HORIZONTAL)
        self.progressbar.Hide()
        self.main_sizer.Add(self.progressbar, 0, wx.ALL | wx.EXPAND, 5)

        # ---------------

        div_separator_panel = wx.Panel(self.main_panel)
        div_separator_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_separator_panel.SetSizer(div_separator_sizer)

        div_separator_statictext = wx.StaticText(div_separator_panel, label='SQLDataForge: RecoveryUnit')
        div_separator_statictext.SetForegroundColour(wx.Colour(150, 150, 150))
        div_separator_sizer.Add(div_separator_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        div_separator_sizer.Add(wx.StaticLine(div_separator_panel), 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.main_sizer.Add(div_separator_panel, 0, wx.EXPAND | wx.TOP, 10)
        # ---------------

        self.buttons_panel = wx.Panel(self.main_panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.cancel_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.CANCEL'])
        self.cancel_button.Bind(wx.EVT_BUTTON, lambda x: self.Destroy())
        self.cancel_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.cancel_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        self.action_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.DO'])
        self.action_button.Disable()
        self.action_button.Bind(wx.EVT_BUTTON, self.recovery_action)
        self.action_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.action_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.action_button, 0, wx.ALL, 5)

        self.main_sizer.Add(self.buttons_panel, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        # ---------------

        self.Layout()


err_code = Recovery.get_last_exit_code()
if err_code == 'E014':
    app = wx.App(False)
    rec = Recovery(0)
    rec.recovery_action()
    app.Destroy()

# Импорт после проверки состояния и восстановления
from app_parameters import APP_TEXT_LABELS
