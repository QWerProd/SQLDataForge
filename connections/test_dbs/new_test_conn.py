import re
import wx
import os
import json
import hashlib
from sshtunnel import HandlerSSHTunnelForwarderError

from connections.test_dbs.type_connectors import *
from app_parameters import APP_TEXT_LABELS, APPLICATION_PATH, APP_PARAMETERS
from app.error_catcher import ErrorCatcher


class NewTestConnection(wx.Dialog):

    curr_page = int
    pages = list
    connector = dict
    type_connection = wx.Panel
    curr_page_panel = wx.Panel
    catcher = ErrorCatcher

    class ChooseConnectorTypePanel(wx.Panel):

        connectors = list

        def set_connectors(self):
            try:
                with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/type_connectors.json'), 'r', encoding='utf-8') as conn_data:
                    data = json.load(conn_data)

                self.connectors = data
            except (FileNotFoundError, PermissionError) as e:
                self.catcher.error_message('E023', str(e))

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

        def set_values(self, connection_info: dict):
            self.db_path_textctrl.SetValue(connection_info.get('database-path', ''))

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

        def get_conn_info(self) -> dict:
            conn_info = {
                'connector-name': self.connector['connector-name'],
                'database-path': self.db_path_textctrl.GetValue()
            }
            return conn_info

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

        connector = dict
        is_ssh_used = bool
        host_info = {
            'database-name': str,
            'database-host': str,
            'database-port': str,
            'database-user': str,
            'database-pass': str
        }
        ssh_info = {
            'ssh-need': bool,
            'ssh-host': str,
            'ssh-port': str,
            'ssh-user': str,
            'ssh-pass': str
        }

        def set_connector(self, connector: dict):
            self.connector = connector
            self.conn_type_statictext.SetLabel(APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'] + ' | ' + self.connector['connector-name'])

        def set_values(self, connection_info: dict):
            db_host, db_port, db_name = re.split(r'[:/]', connection_info['database-path'])
            self.host_path_database_textctrl.SetValue(db_name)
            self.host_path_textctrl.SetValue(db_host)
            self.host_path_port_textctrl.SetValue(db_port)
            self.host_user_name_textctrl.SetValue(connection_info['database-username'])
            self.host_user_password_textctrl.SetValue(connection_info['database-password'])
            self.is_using_ssh_checkbox.SetValue(connection_info['ssh'])
            if connection_info['ssh']:
                ssh_host, ssh_port = re.split(':', connection_info['ssh-path'])
                self.ssh_host_textctrl.SetValue(ssh_host)
                self.ssh_host_port_textctrl.SetValue(ssh_port)
                self.ssh_user_name_textctrl.SetValue(connection_info['ssh-user'])
                self.ssh_user_password_textctrl.SetValue(connection_info['ssh-pass'])
            self.ssh_host_textctrl.Enable(connection_info['ssh'])
            self.ssh_host_port_textctrl.Enable(connection_info['ssh'])
            self.ssh_user_name_textctrl.Enable(connection_info['ssh'])
            self.ssh_user_password_textctrl.Enable(connection_info['ssh'])

        def get_host_info(self) -> dict:
            self.host_info['database-name'] = self.host_path_database_textctrl.GetValue()
            self.host_info['database-host'] = self.host_path_textctrl.GetValue()
            self.host_info['database-port'] = self.host_path_port_textctrl.GetValue()
            self.host_info['database-path'] = f"{self.host_info['database-host']}:{self.host_info['database-port']}/{self.host_info['database-name']}"
            self.host_info['database-user'] = self.host_user_name_textctrl.GetValue()
            self.host_info['database-pass'] = self.host_user_password_textctrl.GetValue()
            return self.host_info

        def get_ssh_info(self) -> dict:
            self.ssh_info['ssh-need'] = self.is_ssh_used
            if self.is_ssh_used:
                self.ssh_info['ssh-host'] = self.ssh_host_textctrl.GetValue()
                self.ssh_info['ssh-port'] = self.ssh_host_port_textctrl.GetValue()
                self.ssh_info['ssh-user'] = self.ssh_user_name_textctrl.GetValue()
                self.ssh_info['ssh-pass'] = self.ssh_user_password_textctrl.GetValue()
            else:
                self.ssh_info['ssh-host'] = None
                self.ssh_info['ssh-port'] = None
                self.ssh_info['ssh-user'] = None
                self.ssh_info['ssh-pass'] = None
            return self.ssh_info

        def is_ssh_checkbox_changed(self, event):
            self.is_ssh_used = self.is_using_ssh_checkbox.GetValue()

            if self.is_ssh_used:
                self.ssh_host_textctrl.Enable()
                self.ssh_host_port_textctrl.Enable()
                self.ssh_user_name_textctrl.Enable()
                self.ssh_user_password_textctrl.Enable()
            else:
                self.ssh_host_textctrl.Disable()
                self.ssh_host_port_textctrl.Disable()
                self.ssh_user_name_textctrl.Disable()
                self.ssh_user_password_textctrl.Disable()

        def get_conn_info(self) -> dict:
            self.get_host_info()
            self.get_ssh_info()
            conn_info = dict(list(self.host_info.items()) + list(self.ssh_info.items()))
            conn_info['connector-name'] = self.connector['connector-name']
            return conn_info

        def __init__(self, parent: wx.Panel):
            super().__init__(parent)
            self.connector = {}
            self.is_ssh_used = False

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

            self.host_info_panel = wx.Panel(self)
            self.host_info_staticbox = wx.StaticBox(self.host_info_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO'])
            self.host_info_sizer = wx.StaticBoxSizer(self.host_info_staticbox, wx.VERTICAL)
            self.host_info_panel.SetSizer(self.host_info_sizer)

            # --------------------

            self.host_path_panel = wx.Panel(self.host_info_panel)
            self.host_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.host_path_panel.SetSizer(self.host_path_sizer)

            self.host_path_database_statictext = wx.StaticText(self.host_path_panel, size=(100, -1),
                                                               label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.HOST_DATABASE'])
            self.host_path_sizer.Add(self.host_path_database_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.host_path_database_textctrl = wx.TextCtrl(self.host_path_panel, size=(125, -1))
            self.host_path_sizer.Add(self.host_path_database_textctrl, 0, wx.EXPAND)

            self.host_path_statictext = wx.StaticText(self.host_path_panel, size=(50, -1),
                                                      label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.HOST_PATH'])
            self.host_path_sizer.Add(self.host_path_statictext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.host_path_textctrl = wx.TextCtrl(self.host_path_panel)
            self.host_path_sizer.Add(self.host_path_textctrl, 1, wx.EXPAND)

            self.host_path_port_statictext = wx.StaticText(self.host_path_panel, size=(40, -1),
                                                           label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.HOST_PORT'])
            self.host_path_sizer.Add(self.host_path_port_statictext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.host_path_port_textctrl = wx.TextCtrl(self.host_path_panel, size=(50, -1))
            self.host_path_port_textctrl.SetValue('5432')
            self.host_path_sizer.Add(self.host_path_port_textctrl, 0, wx.EXPAND)

            self.host_info_sizer.Add(self.host_path_panel, 0, wx.ALL | wx.EXPAND, 5)
            # --------------------

            self.host_user_panel = wx.Panel(self.host_info_panel)
            self.host_user_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.host_user_panel.SetSizer(self.host_user_sizer)

            self.host_user_name_statictext = wx.StaticText(self.host_user_panel, size=(100, -1),
                                                           label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.USER_NAME'])
            self.host_user_sizer.Add(self.host_user_name_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.host_user_name_textctrl = wx.TextCtrl(self.host_user_panel)
            self.host_user_sizer.Add(self.host_user_name_textctrl, 1, wx.EXPAND)

            self.host_user_password_statictext = wx.StaticText(self.host_user_panel, size=(50, -1),
                                                               label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.USER_PASSWORD'])
            self.host_user_sizer.Add(self.host_user_password_statictext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.host_user_password_textctrl = wx.TextCtrl(self.host_user_panel, style=wx.TE_PASSWORD)
            self.host_user_sizer.Add(self.host_user_password_textctrl, 1, wx.EXPAND)

            self.host_info_sizer.Add(self.host_user_panel, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
            # --------------------

            self.sizer.Add(self.host_info_panel, 0, wx.ALL | wx.EXPAND, 10)
            # ----------

            self.is_using_ssh_checkbox = wx.CheckBox(self, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.USE_SSH'])
            self.is_using_ssh_checkbox.Bind(wx.EVT_CHECKBOX, self.is_ssh_checkbox_changed)
            self.sizer.Add(self.is_using_ssh_checkbox, 0, wx.LEFT | wx.TOP, 10)
            # ----------

            self.ssh_info_panel = wx.Panel(self)
            self.ssh_info_staticbox = wx.StaticBox(self.ssh_info_panel, label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.SSH_INFO'])
            self.ssh_info_sizer = wx.StaticBoxSizer(self.ssh_info_staticbox, wx.VERTICAL)
            self.ssh_info_panel.SetSizer(self.ssh_info_sizer)

            # --------------------

            self.ssh_host_panel = wx.Panel(self.ssh_info_panel)
            self.ssh_host_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.ssh_host_panel.SetSizer(self.ssh_host_sizer)

            self.ssh_host_statictext = wx.StaticText(self.ssh_host_panel, size=(100, -1),
                                                     label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.SSH_INFO.HOST'])
            self.ssh_host_sizer.Add(self.ssh_host_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.ssh_host_textctrl = wx.TextCtrl(self.ssh_host_panel)
            self.ssh_host_textctrl.Disable()
            self.ssh_host_sizer.Add(self.ssh_host_textctrl, 1, wx.EXPAND)

            self.ssh_host_port_statictext = wx.StaticText(self.ssh_host_panel, size=(40, -1),
                                                          label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.HOST_PORT'])
            self.ssh_host_sizer.Add(self.ssh_host_port_statictext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.ssh_host_port_textctrl = wx.TextCtrl(self.ssh_host_panel, size=(50, -1))
            self.ssh_host_port_textctrl.Disable()
            self.ssh_host_port_textctrl.SetValue('22')
            self.ssh_host_sizer.Add(self.ssh_host_port_textctrl, 0, wx.EXPAND)

            self.ssh_info_sizer.Add(self.ssh_host_panel, 0, wx.ALL | wx.EXPAND, 5)
            # --------------------

            self.ssh_user_panel = wx.Panel(self.ssh_info_panel)
            self.ssh_user_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.ssh_user_panel.SetSizer(self.ssh_user_sizer)

            self.ssh_user_name_statictext = wx.StaticText(self.ssh_user_panel, size=(100, -1),
                                                          label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.USER_NAME'])
            self.ssh_user_sizer.Add(self.ssh_user_name_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.ssh_user_name_textctrl = wx.TextCtrl(self.ssh_user_panel)
            self.ssh_user_name_textctrl.Disable()
            self.ssh_user_sizer.Add(self.ssh_user_name_textctrl, 1, wx.EXPAND)

            self.ssh_user_password_statictext = wx.StaticText(self.ssh_user_panel, size=(50, -1),
                                                              label=APP_TEXT_LABELS['NEW_TEST_CONN.CONNECT_SERVER.HOST_INFO.USER_PASSWORD'])
            self.ssh_user_sizer.Add(self.ssh_user_password_statictext, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)

            self.ssh_user_password_textctrl = wx.TextCtrl(self.ssh_user_panel, style=wx.TE_PASSWORD)
            self.ssh_user_password_textctrl.Disable()
            self.ssh_user_sizer.Add(self.ssh_user_password_textctrl, 1, wx.EXPAND)

            self.ssh_info_sizer.Add(self.ssh_user_panel, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
            # --------------------

            self.sizer.Add(self.ssh_info_panel, 0, wx.ALL | wx.EXPAND, 10)
            # ----------

    class InternalConnectInformation(wx.Panel):

        connector = dict
        internal_info = dict

        def set_connector(self, connector: dict):
            self.connector = connector
            self.conn_type_statictext.SetLabel(APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'] + ' | ' + self.connector['connector-name'])

        def set_values(self, connection_info: dict, is_hide_type_connector: bool = True):
            if is_hide_type_connector:
                self.connector_type_panel.Hide()
            self.conn_alias_textctrl.SetValue(connection_info['database-alias'])
            self.conn_type_choice.SetSelection(connection_info['database-type-conn'])
            self.conn_desc_textctrl.SetValue(connection_info['database-desc'])

        def get_internal_info(self) -> dict:
            self.internal_info['database-alias'] = self.conn_alias_textctrl.GetValue()
            self.internal_info['database-type-conn'] = self.conn_type_choice.GetSelection()
            self.internal_info['database-desc'] = self.conn_desc_textctrl.GetValue()
            return self.internal_info

        def __init__(self, parent: wx.Panel):
            super().__init__(parent)
            self.connector = {}
            self.internal_info = {}

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

            self.internal_info_panel = wx.Panel(self)
            self.internal_info_staticbox = wx.StaticBox(self.internal_info_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.INTERNAL_INFO'])
            self.internal_info_sizer = wx.StaticBoxSizer(self.internal_info_staticbox, wx.VERTICAL)
            self.internal_info_panel.SetSizer(self.internal_info_sizer)

            # --------------------

            self.main_info_panel = wx.Panel(self.internal_info_panel)
            self.main_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.main_info_panel.SetSizer(self.main_info_sizer)

            self.conn_alias_statictext = wx.StaticText(self.main_info_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_ALIAS'], size=(80, -1))
            self.main_info_sizer.Add(self.conn_alias_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

            self.conn_alias_textctrl = wx.TextCtrl(self.main_info_panel)
            self.main_info_sizer.Add(self.conn_alias_textctrl, 2, wx.EXPAND)

            self.conn_type_choice_statictext = wx.StaticText(self.main_info_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.INTERNAL_INFO.CONN_TYPE'])
            self.main_info_sizer.Add(self.conn_type_choice_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)

            self.conn_type_choice = wx.Choice(self.main_info_panel, choices=APP_TEXT_LABELS['NEW_UDB_WIZARD.INTERNAL_INFO.CONN_TYPE.CHOICES'].split(':'))
            self.main_info_sizer.Add(self.conn_type_choice, 1, wx.EXPAND)

            self.internal_info_sizer.Add(self.main_info_panel, 0, wx.EXPAND | wx.ALL, 5)
            # --------------------

            self.addon_info_panel = wx.Panel(self.internal_info_panel)
            self.addon_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.addon_info_panel.SetSizer(self.addon_info_sizer)

            self.conn_desc_statictext = wx.StaticText(self.addon_info_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_DESC'], size=(80, -1))
            self.addon_info_sizer.Add(self.conn_desc_statictext, 0, wx.RIGHT, 8)

            self.conn_desc_textctrl = wx.TextCtrl(self.addon_info_panel, style=wx.TE_MULTILINE, size=(-1, 75))
            self.addon_info_sizer.Add(self.conn_desc_textctrl, 1, wx.EXPAND)

            self.internal_info_sizer.Add(self.addon_info_panel, 1, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)
            # --------------------

            self.sizer.Add(self.internal_info_panel, 0, wx.EXPAND | wx.ALL, 10)
            # ----------

            self.Layout()

    class ConfirmationConnect(wx.Panel):

        connector = dict
        conn_info = dict

        def set_connection_data(self, connector: dict, conn_data: dict):
            self.connector = connector
            self.conn_info = conn_data
            self.set_values()

        def set_values(self):
            self.conn_type_statictext.SetLabel(APP_TEXT_LABELS['NEW_TEST_CONN.DRIVER'] + ' | ' + self.connector['connector-name'])
            self.db_name_textctrl.SetHint(self.conn_info['database-name'])
            self.db_path_textctrl.SetValue(self.conn_info['database-path'])

        def get_conn_data(self) -> dict:
            db_alias = self.db_name_textctrl.GetValue()
            self.conn_info['database-name'] = db_alias if db_alias != '' else self.db_name_textctrl.GetHint()
            return self.conn_info

        def test_connection(self, event=None):
            conn_name = self.connector['connector-name']
            result = bool

            try:
                result = avaliable_connectors.get(conn_name).test_connection(self.conn_info['database-path'],
                													         self.conn_info.get('database-username', '') + ':' + self.conn_info.get('database-password', ''),
                													         self.conn_info.get('ssh-path', ''),
                													         self.conn_info.get('ssh-user', '') + ':' + self.conn_info.get('ssh-pass', ''))
            except SetSSHTunnelError as e:
                self.catcher.error_message('E022', e.args[2])
            except SetConnectionError as e:
                self.catcher.error_message('E021', e.args[2])

            if result:
                return wx.MessageBox(APP_TEXT_LABELS['NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.MESSAGE'],
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
            elif self.connector['connection-type'] == 'server_host':
                next_page = self.page_server
                self.page_server.set_connector(self.connector)

        if self.curr_page == 1:
            next_page = self.page_internal
            self.type_connection = self.curr_page_panel
            self.page_internal.set_connector(self.connector)

        if self.curr_page == 2:
            next_page = self.page_final
            conn_data = {}
            internal_info = self.page_internal.get_internal_info()
            for key, value in internal_info.items():
                conn_data[key] = value
            if self.type_connection == self.page_local:
                conn_data['database-path'] = self.page_local.get_path()
                conn_data['database-name'] = self.page_local.get_db_name()
                if conn_data['database-path'] == '':
                    return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHOOSE_PATH_ERROR.MESSAGE'],
                                         APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHOOSE_PATH_ERROR.CAPTION'],
                                         wx.ICON_ERROR | wx.OK)
            elif self.type_connection == self.page_server:
                host_info = self.page_server.get_host_info()
                ssh_info = self.page_server.get_ssh_info()
                conn_data['database-host'] = host_info['database-host']
                conn_data['database-port'] = host_info['database-port']
                conn_data['database-path'] = f'{host_info["database-host"]}:{host_info["database-port"]}/{host_info["database-name"]}'
                conn_data['database-name'] = host_info['database-name']
                conn_data['database-username'] = host_info['database-user']
                conn_data['database-password'] = host_info['database-pass']
                conn_data['ssh'] = ssh_info['ssh-need']
                if ssh_info['ssh-need']:
                    conn_data['ssh-path'] = f"{ssh_info['ssh-host']}:{ssh_info['ssh-port']}"
                    conn_data['ssh-user'] = ssh_info['ssh-user']
                    conn_data['ssh-pass'] = ssh_info['ssh-pass']
                if (conn_data['database-name'] == '' or conn_data['database-username'] == '' or
                    conn_data['database-password'] == '' or host_info['database-host'] == '' or
                    host_info['database-port'] == '' or
                        (conn_data['ssh'] and
                            (ssh_info['ssh-host'] is None or ssh_info['ssh-port'] is None or
                                conn_data['ssh-user'] is None or conn_data['ssh-pass'] is None))):
                    return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.FILL_FIELDS.MESSAGE'],
                                         APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.FILL_FIELDS.CAPTION'],
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

        try:
            with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json'), encoding='utf-8') as json_file:
                json_list = json.load(json_file)
        
        except FileNotFoundError:
            with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json'), 'w', encoding='utf-8') as new_file:
                file_input = []
                json.dump(file_input, new_file, sort_keys=True, indent=4)

        except (json.decoder.JSONDecodeError, PermissionError) as e:
            return self.catcher.error_message('E023', str(e))

        curr_test_conn['connector-name'] = self.connector['connector-name']
        curr_test_conn['connection-type'] = self.connector['connection-type']
        for key, value in conn_data.items():
            curr_test_conn[key] = value

        # Формирования хеша для идентификации подключений
        hash_string = ''
        if curr_test_conn['connection-type'] == 'local_file':
            hash_string = curr_test_conn['connector-name'] + curr_test_conn['database-path']
        elif curr_test_conn['connection-type'] == 'server_host':
            hash_string = curr_test_conn['connector-name'] + curr_test_conn['database-path']
            if curr_test_conn['ssh']:
                hash_string += curr_test_conn['ssh-path']
        curr_hash_object = hashlib.sha1(hash_string.encode())
        curr_test_conn['id'] = curr_hash_object.hexdigest()

        # Проверка на уникальность по хешу и имени БД
        for test_conn in json_list:
            if test_conn['id'] == curr_test_conn['id']:
                return wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.TEST_CONN_ALREADY_EXISTS.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.TEST_CONN_ALREADY_EXISTS.CAPTION'],
                                     wx.ICON_WARNING | wx.OK)
            elif test_conn['database-name'] == curr_test_conn['database-name']:
                wx.MessageBox(APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHANGE_DB_NAME.MESSAGE'],
                                     APP_TEXT_LABELS['NEW_TEST_CONN.MESSAGE_BOX.CHANGE_DB_NAME.CAPTION'],
                                     wx.ICON_WARNING | wx.OK)

        json_list.append(curr_test_conn)
        
        try:
            with open(os.path.join(APPLICATION_PATH, 'connections/test_dbs/test_conns.json'), 'w', encoding='utf-8') as json_file:
                json.dump(json_list, json_file, sort_keys=True, indent=4)
        except (PermissionError, FileNotFoundError) as e:
            return self.catcher.error_message('E023', str(e))
        
        self.EndModal(0)

    def __init__(self, parent: wx.Frame):
        super().__init__(parent, title=APP_TEXT_LABELS['NEW_TEST_CONN.TITLE'], size=(700, 500),
                         style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MINIMIZE_BOX)
        self.SetMinSize((700, 500))
        self.SetMaxSize((900, 700))
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.curr_page = 0
        self.connector = {}
        self.pages = []
        self.type_connection = None
        self.catcher = ErrorCatcher(APP_PARAMETERS['APP_LANGUAGE'])

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
        self.page_server = NewTestConnection.ConnectDBServer(self.main_panel)
        self.page_internal = NewTestConnection.InternalConnectInformation(self.main_panel)
        self.page_final = NewTestConnection.ConfirmationConnect(self.main_panel)
        self.main_sizer.Add(self.page_init, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_local, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_server, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_internal, 1, wx.EXPAND)
        self.main_sizer.Add(self.page_final, 1, wx.EXPAND)
        self.page_local.Hide()
        self.page_server.Hide()
        self.page_internal.Hide()
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
