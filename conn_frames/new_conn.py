import wx
import sqlite3

from app.error_catcher import ErrorCatcher

catcher = ErrorCatcher()


class NewConnection(wx.Frame):

    app_conn = sqlite3.Connection

    db_name = ''
    db_path = ''
    db_desc = ''

    is_tested = False

    def file_explore(self, event):
        with wx.FileDialog(self, 'Выбрать файл...', wildcard='Файлы SQLite (*.db)|*.db', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return

            self.db_path = dialog.GetPath()
            self.db_name = dialog.GetFilename()

            self.db_path_textctrl.SetValue(self.db_path)
            self.db_name_textctrl.SetHint(self.db_name)

    def close(self, event):
        if self.db_name == '' and self.db_path == '':
            self.Destroy()
        else:
            result = wx.MessageBox('Введенные данные будут удалены!', 'Вы уверены?', wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if result == wx.OK:
                self.Destroy()
            else:
                return

    def test_connect(self, event):
        self.db_name = self.db_name_textctrl.GetValue()
        self.db_path = self.db_path_textctrl.GetValue()
        self.db_desc = self.db_desc_textctrl.GetValue()

        if self.db_path == '':
            return wx.MessageBox('Введите корректный путь к пБД!', 'Пустой путь', wx.OK | wx.ICON_WARNING)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            result = cursor.execute(f"""SELECT id, posid, table_name, column_name, column_code, column_type, gen_key
                                        FROM t_cases_info
                                        WHERE gen_key IS NOT NULL
                                        AND   column_type IS NOT NULL
                                        AND   column_name IS NOT NULL
                                        AND   posid IS NOT NULL
                                        AND   column_code IS NOT NULL;""").fetchall()
            if len(result) == 0:
                return catcher.error_message('E013')

            wx.MessageBox('Тестовое подключение успешно!', 'Успешное подключение', wx.OK | wx.ICON_INFORMATION)
            self.is_tested = True

        except sqlite3.Error as e:
            catcher.error_message('E012', 'sqlite_errorname: ' + e.sqlite_errorname)

    def apply_changes(self, event):
        self.db_name = self.db_name_textctrl.GetValue()
        self.db_path = self.db_path_textctrl.GetValue()
        self.db_desc = self.db_desc_textctrl.GetValue()

        if self.db_path == '':
            return wx.MessageBox('Введите корректный путь к пБД!', 'Пустой путь', wx.OK | wx.ICON_WARNING)

        field_name = self.db_name_textctrl.GetValue()
        if not self.is_tested:
            dialog = wx.MessageBox('Вы пытаетесь добавить пБД без тестирования подключения!\n'
                                   'Для продолжения работы подтвердите добавление!',
                                   'Подтвердите добавление пБД',
                                   wx.ICON_WARNING | wx.OK | wx.CANCEL)
            if dialog == wx.CANCEL:
                return

        else:
            try:
                cursor = self.app_conn.cursor()
                cursor.execute(f"""INSERT INTO t_databases(dbname, path, field_name, description)
                                   VALUES ("{self.db_name}", "{self.db_path}", "{self.db_name if field_name == '' else field_name}", "{self.db_desc}");""")
                self.app_conn.commit()
                cursor.close()
                wx.MessageBox(f'пБД {self.db_name} успешно добавлена!', 'Успешное добавление', wx.OK | wx.ICON_INFORMATION)
            except sqlite3.Error as e:
                self.app_conn.rollback()
                return catcher.error_message('E014', 'sqlite_errorname: ' + e.sqlite_errorname)

    def __init__(self, app_conn: sqlite3.Connection):
        wx.Frame.__init__(self, None, title='Новое подключение', size=(500, 300),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.FRAME_NO_TASKBAR)
        self.SetMinSize((500, 300))
        self.SetMaxSize((500, 300))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))

        self.app_conn = app_conn

        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        # ---------------

        div_hor_panel = wx.Panel(self.main_panel)
        div_hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_hor_panel.SetSizer(div_hor_sizer)

        # ------------------------------

        image = wx.Image('img/32x32/database  add.png', wx.BITMAP_TYPE_PNG)
        res_img = image.Scale(image.GetWidth() * 2, image.GetHeight() * 2)
        img_bitmap = wx.StaticBitmap(div_hor_panel, bitmap=wx.BitmapFromImage(res_img))
        div_hor_sizer.Add(img_bitmap, 0, wx.LEFT | wx.TOP, 20)

        data_panel = wx.Panel(div_hor_panel)
        data_sizer = wx.BoxSizer(wx.VERTICAL)
        data_panel.SetSizer(data_sizer)

        # ---------------------------------------------

        first_panel = wx.Panel(data_panel)
        first_sizer = wx.BoxSizer(wx.HORIZONTAL)
        first_panel.SetSizer(first_sizer)

        self.db_name_textctrl = wx.TextCtrl(first_panel, size=(-1, 22))
        first_sizer.AddMany([(wx.StaticText(first_panel, label='Имя пБД:', size=(75, -1)), 0, wx.ALIGN_CENTER_VERTICAL, 5),
                             (self.db_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)])

        data_sizer.Add(first_panel, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)
        # ---------------------------------------------

        second_panel = wx.Panel(data_panel)
        second_sizer = wx.BoxSizer(wx.HORIZONTAL)
        second_panel.SetSizer(second_sizer)

        self.db_path_textctrl = wx.TextCtrl(second_panel, size=(-1, 22))
        self.explore_path_button = wx.Button(second_panel, label='...', size=(25, 24), style=wx.NO_BORDER)
        self.explore_path_button.Bind(wx.EVT_BUTTON, self.file_explore)
        second_sizer.AddMany([(wx.StaticText(second_panel, label='Путь к пБД:', size=(75, -1)), 0, wx.ALIGN_CENTER_VERTICAL, 5),
                              (self.db_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                              (self.explore_path_button, 0, wx.ALIGN_CENTER_VERTICAL, 5)])

        data_sizer.Add(second_panel, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)
        # ---------------------------------------------

        third_panel = wx.Panel(data_panel)
        third_sizer = wx.BoxSizer(wx.VERTICAL)
        third_panel.SetSizer(third_sizer)

        self.db_desc_textctrl = wx.TextCtrl(third_panel, style=wx.TE_MULTILINE)
        self.db_desc_textctrl.SetHint('Введите описание пБД...')
        third_sizer.AddMany([(wx.StaticText(third_panel, label='Описание пБД:'), 0, wx.TOP, 5),
                             (self.db_desc_textctrl, 1, wx.BOTTOM | wx.EXPAND, 5)])

        data_sizer.Add(third_panel, 1, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)
        # ---------------------------------------------

        div_hor_sizer.Add(data_panel, 1, wx.ALL | wx.EXPAND, 15)
        # ------------------------------

        self.main_sizer.Add(div_hor_panel, 1, wx.ALL | wx.EXPAND, 0)
        # ---------------

        buttons_panel = wx.Panel(self.main_panel)
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_panel.SetSizer(buttons_sizer)
        buttons_sizer.Add(220, 0, 0)

        self.cancel_button = wx.Button(buttons_panel, label='Отмена', size=(75, -1))
        self.cancel_button.Bind(wx.EVT_BUTTON, self.close)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        self.test_button = wx.Button(buttons_panel, label='Тест...', size=(75, -1))
        self.test_button.Bind(wx.EVT_BUTTON, self.test_connect)
        buttons_sizer.Add(self.test_button, 0, wx.ALL, 5)

        self.apply_button = wx.Button(buttons_panel, label='Применить', size=(75, -1))
        self.apply_button.Bind(wx.EVT_BUTTON, self.apply_changes)
        buttons_sizer.Add(self.apply_button, 0, wx.ALL, 5)

        self.main_sizer.Add(buttons_panel, 0,  wx.TOP | wx.BOTTOM | wx.EXPAND, 5)
        # ---------------
