import wx
import os
import wx.adv
import sqlite3

from app.error_catcher import ErrorCatcher
from app_parameters import APP_TEXT_LABELS, APPLICATION_PATH


class UDBCreateMaster(wx.Frame):

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
        dialog = wx.MessageBox(APP_TEXT_LABELS['NEW_UDB_WIZARD.CANCEL_MESSAGE.MESSAGE'],
                               APP_TEXT_LABELS['MESSAGE_BOX.CAPTION_APPROVE'],
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
            self.previous_button.Unbind(wx.EVT_ENTER_WINDOW)

        if self.page_num == 1:
            self.next_button.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.NEXT'])
            self.next_button.Bind(wx.EVT_BUTTON, self.next_page)

    def next_page(self, event):
        if self.page_num == 0:
            self.db_name, self.db_path = self.page1.get_items()
            if self.db_name == '' or self.db_path == '':
                return wx.MessageBox(APP_TEXT_LABELS['NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.CAPTION'], wx.OK | wx.ICON_ERROR)
        elif self.page_num == 1:
            self.is_adding_enabled, self.db_alias, self.db_desc = self.page2.get_items()
            if self.is_adding_enabled and (self.db_alias == '' or self.db_desc == ''):
                return wx.MessageBox(APP_TEXT_LABELS['NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.CAPTION'], wx.OK | wx.ICON_ERROR)
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
            self.previous_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.previous_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))

        if self.page_num == 2:
            self.next_button.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.FINISH'])
            self.next_button.SetFocus()
            self.next_button.Bind(wx.EVT_BUTTON, self.finish)

    def finish(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        connect = sqlite3.Connection
        cursor = sqlite3.Cursor
        try:
            connect = sqlite3.connect(os.path.join(APPLICATION_PATH, self.db_path, self.db_name))
            cursor = connect.cursor()
            create_db = (f"CREATE TABLE \"t_cases_info\" (\n"
                         f"    \"id\"	INTEGER NOT NULL,\n"
                         f"    \"posid\"	INTEGER NOT NULL UNIQUE,\n"
                         f"	   \"table_name\"	TEXT NOT NULL,\n"
                         f"	   \"column_name\"	TEXT,\n"
                         f"	   \"column_code\"	TEXT DEFAULT NULL UNIQUE,\n"
                         f"	   \"column_type\"	TEXT NOT NULL DEFAULT 'TEXT',\n"
                         f"	   \"gen_key\"	TEXT NOT NULL,\n"
                         f"    \"is_valid\" TEXT NOT NULL DEFAULT 'Y'\n"
                         f"    PRIMARY KEY(\"id\")\n"
                         f");")
            cursor.execute(create_db)
            connect.commit()

            if 'db_alias' in self.dict_db:
                app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))
                app_curs = app_conn.cursor()
                app_curs.execute(f"""INSERT INTO t_databases(dbname, path, field_name, description)
                                     VALUES (\"{self.dict_db['db_name']}\", \"{self.dict_db['db_path']}\", 
                                             \"{self.dict_db['db_alias']}\", \"{self.dict_db['db_desc']}\");""")
                app_conn.commit()
                app_curs.close()
                app_conn.close()

            wx.MessageBox(APP_TEXT_LABELS['NEW_UDB_WIZARD.FINISH.SUCCESS_MESSAGE.MESSAGE'] + self.db_path + "\\" + self.db_name,
                          APP_TEXT_LABELS['NEW_UDB_WIZARD.FINISH.SUCCESS_MESSAGE.CAPTION'], wx.OK | wx.ICON_INFORMATION)
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
            with wx.DirDialog(None, APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DIR_DIALOG'], ) as dir_dialog:
                if dir_dialog.ShowModal() == wx.ID_CANCEL:
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

            header_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.TITLE'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            # ---------------------------------------------

            self.db_name_panel = wx.Panel(self)
            self.db_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_name_panel.SetSizer(self.db_name_sizer)

            db_name_statictext = wx.StaticText(self.db_name_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME'], size=(80, -1))
            self.db_name_sizer.Add(db_name_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.db_name_textctrl = wx.TextCtrl(self.db_name_panel, size=(-1, 22))
            self.db_name_textctrl.SetFocus()
            self.db_name_sizer.Add(self.db_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL, wx.BOTTOM | wx.EXPAND, 10)

            self.data_sizer.Add(self.db_name_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
            # ---------------------------------------------

            self.db_path_panel = wx.Panel(self)
            self.db_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_path_panel.SetSizer(self.db_path_sizer)

            db_path_statictext = wx.StaticText(self.db_path_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_PATH'], size=(80, -1))
            self.db_path_sizer.Add(db_path_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.db_path_textctrl = wx.TextCtrl(self.db_path_panel, size=(-1, 22))
            self.db_path_sizer.Add(self.db_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.explore_path_button = wx.Button(self.db_path_panel, label='...', size=(25, 24), style=wx.NO_BORDER)
            self.explore_path_button.Bind(wx.EVT_BUTTON, self.explore_path)
            self.explore_path_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.explore_path_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            self.db_path_sizer.Add(self.explore_path_button, 0, wx.ALIGN_CENTER_VERTICAL, 10)

            self.data_sizer.Add(self.db_path_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
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
                                              label=APP_TEXT_LABELS['NEW_UDB_WIZARD.SECOND_PAGE.TITLE'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)
            # ------------------------------

            self.div_hor_panel = wx.Panel(self)
            self.div_hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.div_hor_panel.SetSizer(self.div_hor_sizer)

            self.adding_enabled_checkbox = wx.CheckBox(self.div_hor_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.SECOND_PAGE.ADD_IN_SDFORGE'])
            self.adding_enabled_checkbox.SetFocus()
            self.adding_enabled_checkbox.Bind(wx.EVT_CHECKBOX, self.adding_enable)
            self.adding_enabled_checkbox.Bind(wx.EVT_ENTER_WINDOW,
                                              lambda x: self.adding_enabled_checkbox.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            self.div_hor_sizer.Add(self.adding_enabled_checkbox, 0, wx.LEFT | wx.BOTTOM, 10)

            # ------------------------------

            # Обертка для полей ввода
            self.div_vert_panel = wx.Panel(self.div_hor_panel, size=(-1, 250))
            self.div_vert_sizer = wx.BoxSizer(wx.VERTICAL)
            self.div_vert_panel.SetSizer(self.div_vert_sizer)

            self.db_alias_name_panel = wx.Panel(self.div_vert_panel)
            self.db_alias_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_alias_name_panel.SetSizer(self.db_alias_name_sizer)

            db_alias_statictext = wx.StaticText(self.db_alias_name_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.SECOND_PAGE.DB_ALIAS'] + ':', size=(80, -1))
            self.db_alias_name_sizer.Add(db_alias_statictext, 0, wx.ALIGN_CENTER_VERTICAL)

            self.db_alias_textctrl = wx.TextCtrl(self.db_alias_name_panel)
            self.db_alias_name_sizer.Add(self.db_alias_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.div_vert_sizer.Add(self.db_alias_name_panel, 0, wx.EXPAND | wx.BOTTOM | wx.RIGHT, 10)
            self.db_alias_name_panel.Hide()
            # ------------------------------

            self.db_desc_panel = wx.Panel(self.div_vert_panel)
            self.db_desc_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_desc_panel.SetSizer(self.db_desc_sizer)

            db_desc_statictext = wx.StaticText(self.db_desc_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.SECOND_PAGE.DB_DESC'] + ':', size=(80, -1))
            self.db_desc_sizer.Add(db_desc_statictext, 0, wx.ALIGN_CENTER_VERTICAL)

            self.db_desc_textctrl = wx.TextCtrl(self.db_desc_panel, style=wx.TE_MULTILINE | wx.TE_NO_VSCROLL, size=(-1, 75))
            self.db_desc_sizer.Add(self.db_desc_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.div_vert_sizer.Add(self.db_desc_panel, 0, wx.EXPAND | wx.RIGHT, 10)
            self.db_desc_panel.Hide()

            self.div_hor_sizer.Add(self.div_vert_panel, 1, wx.LEFT, 75)
            # ------------------------------

            self.data_sizer.Add(self.div_hor_panel, 0, wx.EXPAND)
            # ---------------

            self.Layout()

    class UDBThirdPage(wx.Panel):

        dict_db = {}

        def set_info(self, db: dict):
            self.dict_db = db

            info_text = (APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_TITLE'] + ":\n"
                         "    " + APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME'] + f" - {self.dict_db['db_name']}\n"
                         "    " + APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_PATH'] + f" - {self.dict_db['db_path']}\n\n")
            if 'db_alias' in self.dict_db:
                info_text += (f"    " + APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_ADDON'] + ":\n"
                              f"        " + APP_TEXT_LABELS['NEW_UDB_WIZARD.SECOND_PAGE.DB_ALIAS'] + f" - {self.dict_db['db_alias']}\n"
                              f"        " + APP_TEXT_LABELS['NEW_UDB_WIZARD.SECOND_PAGE.DB_DESC'] + f" - {self.dict_db['db_desc']}")

            self.info_textctrl.SetValue(info_text)

        def __init__(self, parent: wx.Panel):
            wx.Panel.__init__(self, parent)

            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            info_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_CHECK'])
            self.data_sizer.Add(info_statictext, 0, wx.ALL, 20)

            self.info_textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_READONLY, size=(-1, 400))
            self.data_sizer.Add(self.info_textctrl, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

            self.Layout()

    def __init__(self, catcher: ErrorCatcher):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['NEW_UDB_WIZARD.TITLE'], size=(600, 400),
                          style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MINIMIZE_BOX)
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.SetMinSize((600, 400))
        self.SetMaxSize((800, 550))

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

        header_image = wx.Image(os.path.join(APPLICATION_PATH, 'img/32x32/case.png'), wx.BITMAP_TYPE_PNG)
        header_bitmap = wx.StaticBitmap(header_panel, bitmap=wx.BitmapFromImage(header_image))
        header_sizer.Add(header_bitmap, 0, wx.ALL, 10)

        # ------------------------------

        header_info_panel = wx.Panel(header_panel)
        header_info_sizer = wx.BoxSizer(wx.VERTICAL)
        header_info_panel.SetSizer(header_info_sizer)

        info_header_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.TITLE'])
        info_header_statictext.SetFont(self.small_header_font)
        header_info_sizer.Add(info_header_statictext, 0, wx.ALL)

        info_data_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.INFORMATION'])
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

        div_separator_sizer.Add(wx.StaticLine(div_separator_panel), 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.main_sizer.Add(div_separator_panel, 0, wx.EXPAND)
        # ---------------

        self.buttons_panel = wx.Panel(self.main_panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.cancel_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.CANCEL'])
        self.cancel_button.Bind(wx.EVT_BUTTON, self.cancel)
        self.cancel_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.cancel_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        self.previous_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.PREVIOUS'])
        self.previous_button.Bind(wx.EVT_BUTTON, self.previous_page)
        self.previous_button.Disable()
        self.buttons_sizer.Add(self.previous_button, 0, wx.ALL, 5)

        self.next_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.NEXT'])
        self.next_button.Bind(wx.EVT_BUTTON, self.next_page)
        self.next_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.next_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.next_button, 0, wx.ALL, 5)

        self.main_sizer.Add(self.buttons_panel, 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)
        # ---------------
