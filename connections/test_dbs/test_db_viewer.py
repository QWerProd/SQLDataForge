import wx
import os
import json
import hashlib

from connections.test_dbs.new_test_conn import NewTestConnection
from app.error_catcher import ErrorCatcher
from app_parameters import APP_TEXT_LABELS, APPLICATION_PATH, APP_PARAMETERS

catcher = ErrorCatcher(APP_PARAMETERS['APP_LANGUAGE'])


class TestDBViewer(wx.Frame):

    all_connections = list
    conn_info = dict
    conn_items = dict
    curr_page_panel = wx.Panel
    curr_conn_item = wx.TreeItemId
    curr_item_id = str
    avaliable_info_panels = {
        'local_file': NewTestConnection.ConnectDBLocalFile,
        'server_host': NewTestConnection.ConnectDBServer
    }

    def set_conn_info(self):
        json_data = []
        try:
            with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json')) as json_file:
                json_data = json.load(json_file)

            self.all_connections = json_data
        except FileNotFoundError as e:
            return catcher.error_message('E023', str(e))

    def set_connections_tree_items(self):
        self.treectrl_test_connections.DeleteAllItems()
        for conn_info in self.all_connections:
            tree_item = self.treectrl_test_connections.AppendItem(self.treectrl_test_connections_root, conn_info['database-name'])
            self.conn_items[conn_info['id']] = tree_item
            self.treectrl_test_connections.SetItemImage(tree_item, self.test_dbs_images[conn_info['connector-name']])

    def on_choosed_test_database(self, event):
        if self.curr_conn_item is not None:
            self.treectrl_test_connections.SetItemBold(self.curr_conn_item, False)
        self.curr_conn_item = event.GetItem()
        self.treectrl_test_connections.SetItemBold(self.curr_conn_item, True)

        # Получаем информацию о выбранном тестовом подключении
        self.curr_item_id = ''
        for id_key, treeitem_value in self.conn_items.items():
            if self.curr_conn_item == treeitem_value:
                self.curr_item_id = id_key
                break

        self.set_curr_info_panel(self.curr_item_id)

    def set_curr_info_panel(self, row_id: str):
        conn_data = {}
        for conn_info in self.all_connections:
            if row_id == conn_info['id']:
                conn_data = conn_info
                break

        self.page_init.Hide()
        self.page_internal.Show()
        self.page_internal.set_values(conn_data)
        self.save_button.Enable()
        if conn_data['connection-type'] == 'local_file':
            self.page_server.Show(False)
            self.page_local.Show(True)
            self.curr_page_panel = self.page_local
        elif conn_data['connection-type'] == 'server_host':
            self.page_server.Show(True)
            self.page_local.Show(False)
            self.curr_page_panel = self.page_server
        self.curr_page_panel.set_connector({'connector-name': conn_data['connector-name']})
        self.curr_page_panel.set_values(conn_data)
        self.main_panel.Layout()

    def close(self, event):
        self.Destroy()

    def save_changes(self, event):
        connector_info = self.curr_page_panel.get_conn_info()
        internal_info = self.page_internal.get_internal_info()
        curr_conn_info = dict(list(connector_info.items()) + list(internal_info.items()))
        json_data = []

        # Читаем JSON и отбираем все подключения
        try:
            with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json')) as json_file:
                json_data = json.load(json_file)
        except (json.decoder.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            catcher.error_message('E023', str(e))

        # Перебор подключений и изменение данных
        for conn_info in json_data:
            if conn_info['id'] == self.curr_item_id:
                for key, value in curr_conn_info.items():
                    conn_info[key] = value
                hash_string = str
                if conn_info['connection-type'] == 'local_file':
                    hash_string = curr_conn_info['connector-name'] + curr_conn_info['database-path']
                elif conn_info['connection-type'] == 'server_host':
                    hash_string = curr_conn_info['connector-name'] + curr_conn_info['database-path']
                    if conn_info['ssh']:
                        hash_string += curr_conn_info['ssh-path']
                hash_object = hashlib.sha1(hash_string.encode())
                conn_info['id'] = hash_object.hexdigest()
                self.curr_item_id = hash_object.hexdigest()
                break

        # Перезапись файла JSON
        with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json'), 'w') as json_file:
            json_file.truncate()
            json.dump(json_data, json_file, sort_keys=True, indent=4)

        return wx.MessageBox(APP_TEXT_LABELS['TEST_DB_VIEWER.MESSAGE_BOX.SAVED.MESSAGE'].format(curr_conn_info['database-name']),
                             APP_TEXT_LABELS['TEST_DB_VIEWER.MESSAGE_BOX.SAVED.CAPTION'],
                             wx.ICON_INFORMATION | wx.OK)

    def __init__(self, db_id: str = None):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['TEST_DB_VIEWER.TITLE'], size=(800, 650),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.FRAME_NO_TASKBAR)
        self.SetMinSize((800, 650))
        self.SetMaxSize((1000, 850))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.all_connections = []
        self.conn_items = {}
        self.curr_conn_item = None
        self.curr_item_id = ''
        self.curr_page_panel = None

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.sizer)

        self.treectrl_test_connections = wx.TreeCtrl(self.panel, style=wx.TR_HIDE_ROOT, size=(200, -1))
        self.treectrl_test_connections_root = self.treectrl_test_connections.AddRoot('')

        self.image_connection_items = wx.ImageList(16, 16)
        self.sqlite_image = self.image_connection_items.Add(
            wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/SQLite.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.postgresql_image = self.image_connection_items.Add(
            wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/PostgreSQL.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.mysql_image = self.image_connection_items.Add(
            wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/MySQL.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.treectrl_test_connections.AssignImageList(self.image_connection_items)
        self.test_dbs_images = {
            'SQLite': self.sqlite_image,
            'PostgreSQL': self.postgresql_image,
            'MySQL': self.mysql_image
        }

        self.set_conn_info()
        self.set_connections_tree_items()
        self.treectrl_test_connections.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_choosed_test_database)
        self.sizer.Add(self.treectrl_test_connections, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.TOP, 5)

        # ----------

        self.main_panel = wx.Panel(self.panel)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        # --------------------

        self.page_init = wx.Panel(self.main_panel)
        self.page_local = NewTestConnection.ConnectDBLocalFile(self.main_panel)
        self.page_server = NewTestConnection.ConnectDBServer(self.main_panel)
        self.page_internal = NewTestConnection.InternalConnectInformation(self.main_panel)
        self.main_sizer.Add(self.page_init, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_local, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_server, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_internal, 2, wx.EXPAND)
        self.page_local.Hide()
        self.page_server.Hide()
        self.page_internal.Hide()
        # --------------------

        self.buttons_panel = wx.Panel(self.main_panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.close_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.CLOSE'], size=(75, -1))
        self.close_button.Bind(wx.EVT_BUTTON, self.close)
        self.close_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.close_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.close_button, 0, wx.ALL, 5)

        self.save_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.SAVE'], size=(75, -1))
        self.save_button.Disable()
        self.save_button.Bind(wx.EVT_BUTTON, self.save_changes)
        self.buttons_sizer.Add(self.save_button, 0, wx.ALL, 5)

        self.main_sizer.Add(wx.StaticLine(self.main_panel), 0, wx.ALL | wx.EXPAND, 5)
        self.main_sizer.Add(self.buttons_panel, 0, wx.ALIGN_RIGHT)
        # --------------------

        self.sizer.Add(self.main_panel, 1, wx.EXPAND | wx.ALL, 5)
        # ----------

        if db_id is not None:
            self.set_curr_info_panel(db_id)
        self.Layout()
