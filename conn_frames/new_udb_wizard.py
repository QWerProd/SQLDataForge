import wx
import wx.adv
import sqlite3

from error_catcher import ErrorCatcher


class UDBCreateMaster(wx.Frame):

    app_conn = sqlite3.Connection
    catcher = ErrorCatcher

    is_adding_enabled = False

    db_name = ''
    db_path = ''
    db_alias = ''
    db_desc = ''
    dict_db = {}

    page_num = 0
    pages = []

    def cancel(self, event):
        dialog = wx.MessageBox('Все введенные данные будут неизбежно утеряны!', 'Вы уверены?',
                               wx.OK | wx.CANCEL)
        if dialog == wx.CANCEL:
            return

        self.Destroy()

    def previous_page(self, event):
        self.pages[self.page_num].Hide()
        self.page_num -= 1
        self.pages[self.page_num].Show()
        self.main_data_panel.Layout()

        if self.page_num == 0:
            self.previous_button.Disable()

        if self.page_num == 1:
            self.next_button.SetLabel('Далее ->')
            self.next_button.Bind(wx.EVT_BUTTON, self.next_page)

    def next_page(self, event):
        if self.page_num == 0:
            self.db_name, self.db_path = self.page1.get_items()
            if self.db_name == '' or self.db_path == '':
                return wx.MessageBox('Все поля должны быть заполнены!', 'Заполните поля', wx.OK | wx.ICON_ERROR)
        elif self.page_num == 1:
            self.is_adding_enabled, self.db_alias, self.db_desc = self.page2.get_items()
            if self.is_adding_enabled and (self.db_alias == '' or self.db_desc == ''):
                return wx.MessageBox('Все поля должны быть заполнены!', 'Заполните поля', wx.OK | wx.ICON_ERROR)
            else:
                self.dict_db['db_name'] = self.db_name
                self.dict_db['db_path'] = self.db_path
                if self.is_adding_enabled:
                    self.dict_db['db_alias'] = self.db_alias
                    self.dict_db['db_desc'] = self.db_desc
                self.page3.set_info(self.dict_db)

        self.pages[self.page_num].Hide()
        self.page_num += 1
        self.pages[self.page_num].Show()
        self.main_data_panel.Layout()

        if self.page_num != 0:
            self.previous_button.Enable()

        if self.page_num == 2:
            self.next_button.SetLabel('Готово')
            self.next_button.SetFocus()
            self.next_button.Bind(wx.EVT_BUTTON, self.finish)

    def finish(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        connect = sqlite3.Connection
        cursor = sqlite3.Cursor
        try:
            connect = sqlite3.connect(self.db_path + '/' + self.db_name)
            cursor = connect.cursor()
            create_db = (f"CREATE TABLE \"t_cases_info\" (\n"
                         f"    \"id\"	INTEGER NOT NULL,\n"
                         f"    \"posid\"	INTEGER NOT NULL UNIQUE,\n"
                         f"	   \"table_name\"	TEXT NOT NULL,\n"
                         f"	   \"column_name\"	TEXT,\n"
                         f"	   \"column_code\"	TEXT DEFAULT NULL UNIQUE,\n"
                         f"	   \"column_type\"	TEXT NOT NULL DEFAULT 'TEXT',\n"
                         f"	   \"gen_key\"	TEXT NOT NULL,\n"
                         f"    PRIMARY KEY(\"id\")\n"
                         f");")
            cursor.execute(create_db)
            connect.commit()

            if 'db_alias' in self.dict_db:
                app_curs = self.app_conn.cursor()
                app_curs.execute(f"""INSERT INTO t_databases(dbname, path, field_name, description)
                                     VALUES (\"{self.dict_db['db_name']}\", \"{self.dict_db['db_path']}\", 
                                             \"{self.dict_db['db_alias']}\", \"{self.dict_db['db_desc']}\");""")
                self.app_conn.commit()
                app_curs.close()

            wx.MessageBox('Макет пользовательской Базы Данных создан в ' + self.db_path + "\\" + self.db_name,
                          'Макет пБД создан!', wx.OK | wx.ICON_INFORMATION)
            self.Destroy()
        except sqlite3.Error as e:
            connect.rollback()
            self.catcher.error_message('E012', 'sqlite_errorname: ' + e.sqlite_errorname)
        finally:
            cursor.close()
            connect.close()

    class UDBFirstPage(wx.Panel):

        db_name = ''
        db_path = ''

        def explore_path(self, event):
            with wx.DirDialog(None, 'Укажите путь для пБД...', ) as dir_dialog:
                if dir_dialog.ShowModal() == wx.CANCEL:
                    return

                self.db_path = dir_dialog.GetPath()
                self.db_path_textctrl.SetValue(self.db_path)

        def get_items(self):
            self.db_name = self.db_name_textctrl.GetValue()
            self.db_path = self.db_path_textctrl.GetValue()

            if not self.db_name.endswith('.db'):
                self.db_name += '.db'

            return self.db_name, self.db_path

        def __init__(self, parent: wx.Panel):
            wx.Panel.__init__(self, parent)
            # ------------------------------
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self, label='Укажите имя создаваемого файла и путь, в котором нужно сохранить файл.')
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            # ---------------------------------------------

            self.db_name_panel = wx.Panel(self)
            self.db_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_name_panel.SetSizer(self.db_name_sizer)

            db_name_statictext = wx.StaticText(self.db_name_panel, label='Имя файла:', size=(80, -1))
            self.db_name_sizer.Add(db_name_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.db_name_textctrl = wx.TextCtrl(self.db_name_panel, size=(-1, 22))
            self.db_name_textctrl.SetFocus()
            self.db_name_sizer.Add(self.db_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL, wx.BOTTOM | wx.EXPAND, 10)

            self.data_sizer.Add(self.db_name_panel, 0, wx.EXPAND | wx.ALL, 20)
            # ---------------------------------------------

            self.db_path_panel = wx.Panel(self)
            self.db_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_path_panel.SetSizer(self.db_path_sizer)

            db_path_statictext = wx.StaticText(self.db_path_panel, label='Путь к файлу:', size=(80, -1))
            self.db_path_sizer.Add(db_path_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.db_path_textctrl = wx.TextCtrl(self.db_path_panel, size=(-1, 22))
            self.db_path_sizer.Add(self.db_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL, wx.BOTTOM | wx.EXPAND, 10)

            self.explore_path_button = wx.Button(self.db_path_panel, label='...', size=(25, 24), style=wx.NO_BORDER)
            self.explore_path_button.Bind(wx.EVT_BUTTON, self.explore_path)
            self.db_path_sizer.Add(self.explore_path_button, 0, wx.ALIGN_CENTER_VERTICAL, 10)

            self.data_sizer.Add(self.db_path_panel, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, 20)
            # ---------------------------------------------

            self.Layout()

    class UDBSecondPage(wx.Panel):

        is_adding_enabled = False
        db_alias = ''
        db_desc = ''

        def adding_enable(self, event):
            self.is_adding_enabled = self.adding_enabled_checkbox.GetValue()

            if self.is_adding_enabled:
                self.db_alias_name_panel.Show()
                self.db_desc_panel.Show()
                self.db_alias = self.db_alias_textctrl.GetValue()
                self.db_desc = self.db_desc_textctrl.GetValue()
            else:
                self.db_alias_name_panel.Hide()
                self.db_desc_panel.Hide()
                self.db_alias = ''
                self.db_desc = ''

            self.div_hor_panel.Layout()
            self.div_vert_panel.Layout()

        def get_items(self):
            self.is_adding_enabled = self.adding_enabled_checkbox.GetValue()
            self.db_alias = self.db_alias_textctrl.GetValue()
            self.db_desc = self.db_desc_textctrl.GetValue()
            return self.is_adding_enabled, self.db_alias, self.db_desc

        def __init__(self, parent: wx.Panel):
            wx.Panel.__init__(self, parent)

            # ---------------
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self,
                                              label='Укажите нужно ли добавлять создаваемую пБД в SQLDataForge.\n'
                                                    'Заполните все поля при необходимости.')
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)
            # ------------------------------

            self.div_hor_panel = wx.Panel(self)
            self.div_hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.div_hor_panel.SetSizer(self.div_hor_sizer)

            self.adding_enabled_checkbox = wx.CheckBox(self.div_hor_panel, label='Добавить в SQLDataForge')
            self.adding_enabled_checkbox.SetFocus()
            self.adding_enabled_checkbox.Bind(wx.EVT_CHECKBOX, self.adding_enable)
            self.div_hor_sizer.Add(self.adding_enabled_checkbox, 0, wx.LEFT | wx.BOTTOM, 10)

            # ------------------------------

            # Обертка для полей ввода
            self.div_vert_panel = wx.Panel(self.div_hor_panel, size=(-1, 250))
            self.div_vert_sizer = wx.BoxSizer(wx.VERTICAL)
            self.div_vert_panel.SetSizer(self.div_vert_sizer)

            self.db_alias_name_panel = wx.Panel(self.div_vert_panel)
            self.db_alias_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_alias_name_panel.SetSizer(self.db_alias_name_sizer)

            db_alias_statictext = wx.StaticText(self.db_alias_name_panel, label='Псевдоним:', size=(80, -1))
            self.db_alias_name_sizer.Add(db_alias_statictext, 0, wx.ALIGN_CENTER_VERTICAL)

            self.db_alias_textctrl = wx.TextCtrl(self.db_alias_name_panel)
            self.db_alias_name_sizer.Add(self.db_alias_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.div_vert_sizer.Add(self.db_alias_name_panel, 0, wx.EXPAND | wx.BOTTOM | wx.RIGHT, 10)
            self.db_alias_name_panel.Hide()
            # ------------------------------

            self.db_desc_panel = wx.Panel(self.div_vert_panel)
            self.db_desc_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_desc_panel.SetSizer(self.db_desc_sizer)

            db_desc_statictext = wx.StaticText(self.db_desc_panel, label='Описание:', size=(80, -1))
            self.db_desc_sizer.Add(db_desc_statictext, 0, wx.ALIGN_CENTER_VERTICAL)

            self.db_desc_textctrl = wx.TextCtrl(self.db_desc_panel, style=wx.TE_MULTILINE | wx.TE_NO_VSCROLL, size=(-1, 75))
            self.db_desc_sizer.Add(self.db_desc_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.div_vert_sizer.Add(self.db_desc_panel, 0, wx.EXPAND | wx.RIGHT, 10)
            self.db_desc_panel.Hide()

            self.div_hor_sizer.Add(self.div_vert_panel, 1, wx.LEFT, 100)
            # ------------------------------

            self.data_sizer.Add(self.div_hor_panel, 0, wx.EXPAND)
            # ---------------

            self.Layout()

    class UDBThirdPage(wx.Panel):

        dict_db = {}

        def set_info(self, db: dict):
            self.dict_db = db

            info_text = (f"Информация о файле:\n"
                         f"    Имя файла - {self.dict_db['db_name']}\n"
                         f"    Путь к файлу - {self.dict_db['db_path']}\n\n")
            if 'db_alias' in self.dict_db:
                info_text += (f"    Дополнительная информация:\n"
                              f"        Псевдоним - {self.dict_db['db_alias']}\n"
                              f"        Описание - {self.dict_db['db_desc']}")

            self.info_textctrl.SetValue(info_text)

        def __init__(self, parent: wx.Panel):
            wx.Panel.__init__(self, parent)

            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            info_statictext = wx.StaticText(self, label='Проверьте правильность указанных данных.')
            self.data_sizer.Add(info_statictext, 0, wx.ALL, 20)

            self.info_textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_READONLY, size=(-1, 400))
            self.data_sizer.Add(self.info_textctrl, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

            self.Layout()

    def __init__(self, app_conn: sqlite3.Connection, catcher: ErrorCatcher):
        wx.Frame.__init__(self, None, title='Мастер создания пБД', size=(600, 350),
                          style=wx.FRAME_NO_TASKBAR | wx.CLOSE_BOX | wx.FRAME_TOOL_WINDOW | wx.CAPTION)
        self.SetMinSize((600, 350))
        self.SetMaxSize((600, 350))

        self.app_conn = app_conn
        self.catcher = catcher

        self.small_header_font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.header_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, 0, 500, faceName='Verdana')

        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        # ---------------

        header_panel = wx.Panel(self.main_panel)
        header_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_panel.SetSizer(header_sizer)

        header_image = wx.Image('img/32x32/case.png', wx.BITMAP_TYPE_PNG)
        header_bitmap = wx.StaticBitmap(header_panel, bitmap=wx.BitmapFromImage(header_image))
        header_sizer.Add(header_bitmap, 0, wx.ALL, 10)

        # ------------------------------

        header_info_panel = wx.Panel(header_panel)
        header_info_sizer = wx.BoxSizer(wx.VERTICAL)
        header_info_panel.SetSizer(header_info_sizer)

        info_header_statictext = wx.StaticText(header_info_panel, label='Мастер создания пБД')
        info_header_statictext.SetFont(self.small_header_font)
        header_info_sizer.Add(info_header_statictext, 0, wx.ALL)

        info_data_statictext = wx.StaticText(header_info_panel, label='Данный мастер предназначен для создания рабочего каркаса пБД')
        header_info_sizer.Add(info_data_statictext, 0, wx.ALL)

        header_sizer.Add(header_info_panel, 0, wx.ALL, 10)
        # ------------------------------

        self.main_sizer.Add(header_panel, 0, wx.EXPAND)
        self.main_sizer.Add(wx.StaticLine(self.main_panel), 0, wx.EXPAND)
        # ---------------

        self.main_data_panel = wx.Panel(self.main_panel)
        self.main_data_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_data_panel.SetSizer(self.main_data_sizer)

        self.page1 = self.UDBFirstPage(self.main_data_panel)
        self.page2 = self.UDBSecondPage(self.main_data_panel)
        self.page3 = self.UDBThirdPage(self.main_data_panel)

        self.pages.append(self.page1)
        self.pages.append(self.page2)
        self.pages.append(self.page3)

        self.main_data_sizer.Add(self.page1, 0, wx.EXPAND)
        self.main_data_sizer.Add(self.page2, 0, wx.EXPAND)
        self.main_data_sizer.Add(self.page3, 0, wx.EXPAND)
        self.page2.Hide()
        self.page3.Hide()

        self.main_sizer.Add(self.main_data_panel, 1, wx.EXPAND)
        # ---------------

        div_separator_panel = wx.Panel(self.main_panel)
        div_separator_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_separator_panel.SetSizer(div_separator_sizer)

        div_separator_statictext = wx.StaticText(div_separator_panel, label='SQLDataForge: UDBCreateWizard')
        div_separator_statictext.SetForegroundColour(wx.Colour(150, 150, 150))
        div_separator_sizer.Add(div_separator_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        div_separator_sizer.Add(wx.StaticLine(div_separator_panel), 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.main_sizer.Add(div_separator_panel, 0, wx.EXPAND)
        # ---------------

        self.buttons_panel = wx.Panel(self.main_panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.buttons_sizer.Add(320, 0, 0)

        self.cancel_button = wx.Button(self.buttons_panel, label='Отмена')
        self.cancel_button.Bind(wx.EVT_BUTTON, self.cancel)
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        self.previous_button = wx.Button(self.buttons_panel, label='<- Назад')
        self.previous_button.Bind(wx.EVT_BUTTON, self.previous_page)
        self.previous_button.Disable()
        self.buttons_sizer.Add(self.previous_button, 0, wx.ALL, 5)

        self.next_button = wx.Button(self.buttons_panel, label='Далее ->')
        self.next_button.Bind(wx.EVT_BUTTON, self.next_page)
        self.buttons_sizer.Add(self.next_button, 0, wx.ALL, 5)

        self.main_sizer.Add(self.buttons_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        # ---------------
