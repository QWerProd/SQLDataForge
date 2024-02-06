import wx
import os
import json
import hashlib

from app_parameters import APP_TEXT_LABELS, APPLICATION_PATH


class NewTestConnection(wx.Dialog):

    curr_page = int
    pages = list
    connector = dict
    curr_page_panel = wx.Panel

    class ChooseConnectorTypePanel(wx.Panel):

        connectors = list

        def set_connectors(self):
            with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/connectors.json'), 'r') as conn_data:
                data = json.load(conn_data)

            self.connectors = data

        def set_items(self):
            # Установка листа картинок
            imagelist = wx.ImageList(96, 96, True)
            imgs = []
            for connector in self.connectors:
                img = wx.Image(os.path.join(APPLICATION_PATH, connector['connector-logo']), wx.BITMAP_TYPE_PNG)
                done_img = img.Scale(96, 96, wx.IMAGE_QUALITY_HIGH)
                imgb = imagelist.Add(wx.BitmapFromImage(done_img))
                imgs.append(imgb)
            self.connectors_listctrl.AssignImageList(imagelist, wx.IMAGE_LIST_NORMAL)

            # Установка элементов
            for i in range(len(self.connectors)):
                self.connectors_listctrl.InsertItem(i, self.connectors[i]['connector-name'], imgs[i])

        def get_connector(self) -> dict:
            item_index = self.connectors_listctrl.GetFocusedItem()
            if item_index != -1:
                return self.connectors[item_index]
            else:
                return item_index

        def __init__(self, parent: wx.Panel):
            super().__init__(parent)

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            title_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['NEW_TEST_CONN.CHOOSE_CONNECTOR.TITLE'])
            self.sizer.Add(title_statictext, 0, wx.LEFT | wx.TOP | wx.RIGHT, 20)

            self.connectors_listctrl = wx.ListCtrl(self, style=wx.LC_ICON)
            self.set_connectors()
            self.set_items()
            self.sizer.Add(self.connectors_listctrl, 1, wx.ALL | wx.EXPAND, 10)

    class ConnectDBLocalFile(wx.Panel):

        connector = dict
        db_path = str
        db_name = str

        def set_connector(self, connector: dict):
            self.connector = connector
            self.conn_type_statictext.SetLabel(APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'] + ' | ' + self.connector['connector-name'])

        def file_explore(self, event):
            with wx.FileDialog(self, APP_TEXT_LABELS['FILE_DIALOG.CAPTION_CHOOSE'],
                               wildcard=APP_TEXT_LABELS['FILE_DIALOG.WILDCARD_DB'],
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
                if dialog.ShowModal() == wx.ID_CANCEL:
                    return

                self.db_path = dialog.GetPath()
                self.db_name = dialog.GetFilename()
                self.db_path_textctrl.SetValue(self.db_path)

        def get_path(self) -> str: return self.db_path

        def get_db_name(self) -> str: return self.db_name

        def __init__(self, parent: wx.Panel):
            super().__init__(parent)
            self.connector = {}
            self.db_path = ''

            self.driver_font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            # ----------
            self.connector_type_panel = wx.Panel(self)
            self.connector_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.connector_type_panel.SetSizer(self.connector_type_sizer)

            self.conn_type_statictext = wx.StaticText(self.connector_type_panel,
                                                      label=APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'])
            self.conn_type_statictext.SetFont(self.driver_font)
            self.connector_type_sizer.Add(self.conn_type_statictext, 0, wx.LEFT, 10)

            self.sizer.Add(self.connector_type_panel, 0, wx.ALL | wx.EXPAND, 5)
            self.sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
            # ----------

            self.data_panel = wx.Panel(self)
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.data_panel.SetSizer(self.data_sizer)

            # --------------------

            self.db_info_panel = wx.Panel(self.data_panel)
            db_info_staticbox = wx.StaticBox(self.db_info_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_LOCAL.DB_INFO'])
            self.db_info_sizer = wx.StaticBoxSizer(db_info_staticbox, wx.VERTICAL)
            self.db_info_panel.SetSizer(self.db_info_sizer)

            # ------------------------------

            self.db_path_panel = wx.Panel(self.db_info_panel)
            self.db_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_path_panel.SetSizer(self.db_path_sizer)

            db_path_statictext = wx.StaticText(self.db_path_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_LOCAL.DB_PATH'])
            self.db_path_sizer.Add(db_path_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.db_path_textctrl = wx.TextCtrl(self.db_path_panel, size=(-1, 22))
            self.db_path_sizer.Add(self.db_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.explore_path_button = wx.Button(self.db_path_panel, label='...', size=(25, 24), style=wx.NO_BORDER)
            self.explore_path_button.Bind(wx.EVT_ENTER_WINDOW,
                                          lambda x: self.explore_path_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            self.explore_path_button.Bind(wx.EVT_BUTTON, self.file_explore)
            self.db_path_sizer.Add(self.explore_path_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

            self.db_info_sizer.Add(self.db_path_panel, 0, wx.EXPAND | wx.ALL, 5)
            # ------------------------------

            self.data_sizer.Add(self.db_info_panel, 0, wx.EXPAND | wx.ALL, 10)
            # --------------------

            self.sizer.Add(self.data_panel, 1, wx.EXPAND)
            # ----------

    class ConnectDBServer(wx.Panel):

        def __init__(self, parent: wx.Panel):
            super().__init__(parent)

    class ConfirmationConnect(wx.Panel):

        connector = dict
        conn_info = dict

        def set_connection_data(self, connector: dict, conn_data: dict):
            self.connector = connector
            self.conn_info = conn_data
            self.set_values()

        def set_values(self):
            self.conn_type_statictext.SetLabel(APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'] + ' | ' + self.connector['connector-name'])
            self.db_name_textctrl.SetHint(self.conn_info['db-name'])
            self.db_path_textctrl.SetValue(self.conn_info['db-path'])

        def get_conn_data(self) -> dict:
            db_alias = self.db_name_textctrl.GetValue()
            self.conn_info['db-name'] = db_alias if db_alias != '' else self.db_name_textctrl.GetHint()
            return self.conn_info

        def test_connection(self, event=None):
            conn_type = self.connector['connection-type']
            conn_name = self.connector['connector-name']

            if conn_type == 'local_file':
                if conn_name == 'SQLite':
                    import sqlite3
                    file_path = self.conn_info['db-path']
                    try:
                        test_conn = sqlite3.connect(file_path)
                        test_conn.close()
                    except sqlite3.Error as e:
                        return wx.MessageBox(e.sqlite_errorcode + ': ' + e.sqlite_errorname + '\n' + e.args[0],
                                             APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.TEST_ERROR.CAPTION'],
                                             wx.ICON_ERROR | wx.OK)

            wx.MessageBox(APP_TEXT_LABELS['NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.MESSAGE'],
                          APP_TEXT_LABELS['NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.CAPTION'],
                          wx.ICON_INFORMATION | wx.OK)

        def __init__(self, parent: wx.Panel):
            super().__init__(parent)
            self.connector = {}
            self.conn_info = {}

            self.driver_font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            # ----------

            self.connector_type_panel = wx.Panel(self)
            self.connector_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.connector_type_panel.SetSizer(self.connector_type_sizer)

            self.conn_type_statictext = wx.StaticText(self.connector_type_panel,
                                                      label=APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'])
            self.conn_type_statictext.SetFont(self.driver_font)
            self.connector_type_sizer.Add(self.conn_type_statictext, 0, wx.LEFT, 10)

            self.sizer.Add(self.connector_type_panel, 0, wx.ALL | wx.EXPAND, 5)
            self.sizer.Add(wx.StaticLine(self, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
            # ----------

            self.check_info_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_CHECK'])
            self.sizer.Add(self.check_info_statictext, 0, wx.ALL, 20)

            # ----------

            self.db_info_panel = wx.Panel(self)
            db_info_staticbox = wx.StaticBox(self.db_info_panel,
                                             label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_LOCAL.DB_INFO'])
            self.db_info_sizer = wx.StaticBoxSizer(db_info_staticbox, wx.VERTICAL)
            self.db_info_panel.SetSizer(self.db_info_sizer)

            # ----------------------

            self.db_path_panel = wx.Panel(self.db_info_panel)
            self.db_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.db_path_panel.SetSizer(self.db_path_sizer)

            db_name_statictext = wx.StaticText(self.db_path_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONFIRM_CONN.DB_NAME'])
            self.db_path_sizer.Add(db_name_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.db_name_textctrl = wx.TextCtrl(self.db_path_panel, size=(100, 22))
            self.db_path_sizer.Add(self.db_name_textctrl, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

            self.db_path_sizer.Add(wx.StaticLine(self.db_path_panel, style=wx.LI_VERTICAL), 0, wx.EXPAND)

            db_path_statictext = wx.StaticText(self.db_path_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_LOCAL.DB_PATH'])
            self.db_path_sizer.Add(db_path_statictext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.db_path_textctrl = wx.TextCtrl(self.db_path_panel, size=(-1, 22))
            self.db_path_textctrl.Disable()
            self.db_path_sizer.Add(self.db_path_textctrl, 1, wx.EXPAND)

            self.db_info_sizer.Add(self.db_path_panel, 1, wx.EXPAND | wx.ALL, 5)
            self.db_info_sizer.Add(wx.StaticLine(self.db_info_panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)
            # ----------------------

            self.buttons_panel = wx.Panel(self.db_info_panel)
            self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.buttons_panel.SetSizer(self.buttons_sizer)

            self.test_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.TEST'], size=(75, -1))
            self.test_button.Bind(wx.EVT_BUTTON, self.test_connection)
            self.buttons_sizer.Add(self.test_button)

            self.db_info_sizer.Add(self.buttons_panel, 1, wx.ALIGN_RIGHT | wx.ALL, 5)
            # ----------------------

            self.sizer.Add(self.db_info_panel, 0, wx.EXPAND | wx.ALL, 10)
            # -----------

    def cancel(self, event):
        self.EndModal(0)

    def previous_page(self, event):
        self.curr_page -= 1
        self.curr_page_panel.Hide()
        prev_page = self.pages[self.curr_page]
        prev_page.Show()
        self.pages.remove(prev_page)
        self.curr_page_panel = prev_page
        self.main_panel.Layout()
        if self.curr_page == 0:
            self.previous_button.Disable()
        if self.curr_page <= 1:
            self.next_button.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.NEXT'])
            self.next_button.Bind(wx.EVT_BUTTON, self.next_page)

    def next_page(self, event):
        next_page = wx.Panel
        if self.curr_page == 0:
            self.connector = self.page_init.get_connector()
            if self.connector == -1:
                return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.EMPTY_CONNECTOR.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.EMPTY_CONNECTOR.CAPTION'],
                                     wx.ICON_ERROR | wx.OK_DEFAULT)

            if self.connector['connection-type'] == 'local_file':
                next_page = self.page_local
                self.page_local.set_connector(self.connector)
            else:
                pass
        if self.curr_page == 1:
            next_page = self.page_final
            conn_data = {}
            if self.curr_page_panel == self.page_local:
                conn_data['db-path'] = self.page_local.get_path()
                conn_data['db-name'] = self.page_local.get_db_name()
                if conn_data['db-path'] == '':
                    return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHOOSE_PATH_ERROR.MESSAGE'],
                                         APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHOOSE_PATH_ERROR.CAPTION'],
                                         wx.ICON_ERROR | wx.OK)
            self.page_final.set_connection_data(self.connector, conn_data)
            self.next_button.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.FINISH'])
            self.next_button.Bind(wx.EVT_BUTTON, self.finish)

        self.curr_page += 1
        self.curr_page_panel.Hide()
        next_page.Show()
        self.pages.append(self.curr_page_panel)
        self.curr_page_panel = next_page
        self.main_panel.Layout()

        self.previous_button.Enable()

    def finish(self, event):
        json_list = []
        curr_test_conn = {}
        conn_data = self.page_final.get_conn_data()
        with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json')) as json_file:
            try:
                json_list = json.load(json_file)
            except json.decoder.JSONDecodeError:
                pass

        curr_test_conn['connector-name'] = self.connector['connector-name']
        curr_test_conn['connection-type'] = self.connector['connection-type']
        for key, value in conn_data.items():
            curr_test_conn[key] = value

        # Формирования хеша для идентификации подключений
        hash_string = ''
        if curr_test_conn['connection-type'] == 'local_file':
            hash_string = curr_test_conn['connector-name'] + curr_test_conn['db-path']
        curr_hash_object = hashlib.sha1(hash_string.encode())
        curr_test_conn['id'] = curr_hash_object.hexdigest()

        # Проверка на уникальность по хешу и имени БД
        for test_conn in json_list:
            if test_conn['id'] == curr_test_conn['id']:
                return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.TEST_CONN_ALREADY_EXISTS.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.TEST_CONN_ALREADY_EXISTS.CAPTION'],
                                     wx.ICON_WARNING | wx.OK)
            elif test_conn['db-name'] == curr_test_conn['db-name']:
                return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHANGE_DB_NAME.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHANGE_DB_NAME.CAPTION'],
                                     wx.ICON_WARNING, wx.OK)

        json_list.append(curr_test_conn)
        with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json'), 'w') as json_file:
            json.dump(json_list, json_file, sort_keys=True, indent=4)
        self.EndModal(0)

    def __init__(self, parent: wx.Frame):
        super().__init__(parent, title=APP_TEXT_LABELS['NEW_TEST_CONN.TITLE'], size=(700, 500))
        self.SetMinSize((700, 500))
        self.SetMaxSize((700, 500))
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.curr_page = 0
        self.connector = {}
        self.pages = []

        self.small_header_font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.header_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, 0, 500, faceName='Verdana')

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        # ----------

        header_panel = wx.Panel(self.panel)
        header_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_panel.SetSizer(header_sizer)

        header_image = wx.Image(os.path.join(APPLICATION_PATH, 'img/32x32/key.png'), wx.BITMAP_TYPE_PNG)
        header_bitmap = wx.StaticBitmap(header_panel, bitmap=wx.BitmapFromImage(header_image))
        header_sizer.Add(header_bitmap, 0, wx.ALL, 10)

        # --------------------

        header_info_panel = wx.Panel(header_panel)
        header_info_sizer = wx.BoxSizer(wx.VERTICAL)
        header_info_panel.SetSizer(header_info_sizer)

        info_header_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.HEADER'])
        info_header_statictext.SetFont(self.small_header_font)
        header_info_sizer.Add(info_header_statictext, 0, wx.ALL)

        info_data_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.HEADER2'])
        header_info_sizer.Add(info_data_statictext, 0, wx.ALL)

        header_sizer.Add(header_info_panel, 0, wx.ALL, 10)
        # --------------------

        self.sizer.Add(header_panel, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND)
        # ----------

        self.main_panel = wx.Panel(self.panel)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        self.page_init = NewTestConnection.ChooseConnectorTypePanel(self.main_panel)
        self.curr_page_panel = self.page_init
        self.page_local = NewTestConnection.ConnectDBLocalFile(self.main_panel)
        self.page_final = NewTestConnection.ConfirmationConnect(self.main_panel)
        self.main_sizer.Add(self.page_init, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_local, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_final, 1, wx.EXPAND)
        self.page_local.Hide()
        self.page_final.Hide()

        self.sizer.Add(self.main_panel, 1, wx.EXPAND)
        # -----------

        div_separator_panel = wx.Panel(self.main_panel)
        div_separator_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_separator_panel.SetSizer(div_separator_sizer)

        div_separator_statictext = wx.StaticText(div_separator_panel, label='SQLDataForge: NewTestConnection')
        div_separator_statictext.SetForegroundColour(wx.Colour(150, 150, 150))
        div_separator_sizer.Add(div_separator_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        div_separator_sizer.Add(wx.StaticLine(div_separator_panel), 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.main_sizer.Add(div_separator_panel, 0, wx.EXPAND)
        # ----------

        self.buttons_panel = wx.Panel(self.panel)
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

        self.sizer.Add(self.buttons_panel, 0, wx. BOTTOM | wx.ALIGN_RIGHT, 5)
        # ----------

        self.Layout()
