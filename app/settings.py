import sqlite3

import wx.stc
import wx.lib.scrolledpanel

from app.settings_entries import *
from app.app_parameters import APP_PARAMETERS


class Settings(wx.Dialog):

    parent = wx.Frame
    app_conn = sqlite3.Connection

    prev_page = None

    sett_items = dict
    changed_params = dict
    changed_params_journal = dict
    treectrl_items = list
    parent_items = list
    curr_param_items = list

    def set_settings_items(self):
        curs = self.app_conn.cursor()
        id_parents = curs.execute(f"""SELECT id, sett_label
                                      FROM t_settings_items
                                      WHERE id_fk IS NULL
                                      AND is_valid = 'Y'
                                      ORDER BY id;""").fetchall()

        for parent in id_parents:
            self.sett_items[(parent[0], parent[1])] = []
            self.parent_items.append(parent[1])
            id_childrens = curs.execute(f"""SELECT id, sett_label
                                            FROM t_settings_items
                                            WHERE id_fk = {parent[0]}
                                            AND is_valid = 'Y'
                                            ORDER BY id;""").fetchall()
            for child in id_childrens:
                self.sett_items[(parent[0], parent[1])].append((child[0], child[1]))

        root = self.settings_items_treectrl.AddRoot('')

        for key, value in self.sett_items.items():
            menu_root = self.settings_items_treectrl.AppendItem(root, key[1])
            self.settings_items_treectrl.SetItemBold(menu_root, True)
            self.treectrl_items.append((key[0], menu_root))
            for child in value:
                child_item = self.settings_items_treectrl.AppendItem(menu_root, child[1])
                self.treectrl_items.append((child[0], child_item))

        self.settings_items_treectrl.ExpandAll()

    def set_setting_page(self, event=None, menu_name=None):
        if event is not None:
            item = event.GetItem()
            menu_name = self.settings_items_treectrl.GetItemText(item)
        else:
            menu_name = menu_name
        if event is not None and menu_name in self.parent_items:
            self.settings_items_treectrl.UnselectItem(item)
        else:
            is_changed = False
            self.set_params(menu_name)
            self.curr_param_items.clear()
            self.settings_item_panel.DestroyChildren()

            curs = self.app_conn.cursor()
            entries = curs.execute(f"""SELECT p.param_name, sip.entry_type, sip.entry_label, sip.entry_choices, p.param_value
                                       FROM t_settings_items_params as sip
                                       JOIN t_settings_items as si ON sip.id_parent = si.id
                                       LEFT JOIN t_params as p ON sip.id_param = p.id
                                       WHERE si.sett_label = '{menu_name}'
                                       AND   sip.is_valid = 'Y'
                                       AND   si.is_valid = 'Y'
                                       ORDER BY sip.posid;""").fetchall()

            for entry in entries:
                menu_entry_panel = None
                if entry[1] == 'CheckboxPoint':
                    menu_entry_panel = CheckboxPoint(self.settings_item_panel, entry[2])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL, 2)
                elif entry[1] == 'RadioSelect':
                    menu_entry_panel = RadioSelect(self.settings_item_panel, entry[2], entry[3])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL, 2)
                elif entry[1] == 'SelectorBox':
                    menu_entry_panel = SelectorBox(self.settings_item_panel, entry[2], list(entry[3].split(':')))
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL | wx.EXPAND, 2)
                elif entry[1] == 'HEXEnter':
                    menu_entry_panel = HEXEnter(self.settings_item_panel, entry[2])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL | wx.EXPAND, 2)
                elif entry[1] == 'HeaderGroup':
                    menu_entry_panel = HeaderGroup(self.settings_item_panel, entry[2])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL | wx.EXPAND, 5)
                elif entry[1] == 'SpinNumber':
                    menu_entry_panel = SpinNumber(self.settings_item_panel, entry[2], list(entry[3].split(':')))
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL | wx.EXPAND, 2)
                elif entry[1] == 'CodeRedactor':
                    menu_entry_panel = CodeRedactor(self.settings_item_panel)
                    self.settings_item_sizer.Add(menu_entry_panel, 1, wx.ALL | wx.EXPAND, 5)

                if menu_name in self.changed_params.keys():
                    if entry[0] in self.changed_params[menu_name].keys():
                        menu_entry_panel.set_value(self.changed_params[menu_name][entry[0]])
                        is_changed = True
                if not is_changed:
                    menu_entry_panel.set_value(entry[4])
                self.curr_param_items.append((entry[0], menu_entry_panel))

            self.settings_item_panel.Layout()

    def set_params(self, next_menu_name: str = None):
        if next_menu_name is None:
            item = self.settings_items_treectrl.GetSelection()
            menu_item = self.settings_items_treectrl.GetItemText(item)
            self.prev_page = None
        else:
            menu_item = next_menu_name

        if menu_item not in self.changed_params.keys():
            self.changed_params[menu_item] = {}
            self.changed_params_journal[menu_item] = {}
        for param_entry in self.curr_param_items:
            if param_entry[0] is not None:
                param_value = param_entry[1].param
                if self.prev_page is not None and APP_PARAMETERS[param_entry[0]] != str(param_value):
                    self.changed_params[self.prev_page][param_entry[0]] = str(param_value)
                    self.changed_params_journal[self.prev_page][param_entry[0]] = str(param_value)
                elif APP_PARAMETERS[param_entry[0]] != str(param_value):
                    self.changed_params[menu_item][param_entry[0]] = str(param_value)
                    self.changed_params_journal[menu_item][param_entry[0]] = str(param_value)

        self.prev_page = menu_item

    def close(self, event):
        for values in self.changed_params.values():
            if len(values.keys()) > 0:
                dlg = wx.MessageBox('Все несохраненные изменения будут удалены!', 'Подтвердите выход',
                                    wx.YES_NO | wx.NO_DEFAULT)
                if dlg == wx.YES:
                    self.EndModal(0)
                else:
                    return
            else:
                continue
        self.EndModal(0)

    def apply(self, event):
        self.change_settings()

    def apply_close(self, event):
        self.change_settings()
        self.EndModal(1)

    def change_settings(self):
        curs = self.app_conn.cursor()
        self.set_params()
        for entry_page_name, entry_page_params in self.changed_params.items():
            for entry_name, entry_value in entry_page_params.items():
                curs.execute(f"""UPDATE t_params
                                 SET    param_value = '{entry_value}'
                                 WHERE  param_name = '{entry_name}';""")
                self.app_conn.commit()
                APP_PARAMETERS[entry_name] = entry_value
        self.changed_params.clear()
        self.set_setting_page(menu_name=self.prev_page)
        curs.close()

    def __init__(self, parent: wx.Frame, app_conn: sqlite3.Connection):
        super().__init__(parent, title='Настройки', size=(700, 500),
                         style=wx.CAPTION | wx.CLOSE_BOX)
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))
        self.Bind(wx.EVT_CLOSE, self.close)
        self.app_conn = app_conn
        self.sett_items = {}
        self.changed_params = {}
        self.changed_params_journal = {}
        self.treectrl_items = []
        self.parent_items = []
        self.curr_param_items = []

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        # ---------------

        self.main_splitter = wx.SplitterWindow(self.panel, wx.SP_LIVE_UPDATE)

        # ------------------------------

        self.settings_items_treectrl = wx.TreeCtrl(self.main_splitter,
                                                   style=wx.TR_HIDE_ROOT | wx.TR_NO_LINES | wx.TR_SINGLE | wx.TR_FULL_ROW_HIGHLIGHT)
        self.settings_items_treectrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.set_setting_page)
        self.set_settings_items()

        # ------------------------------

        self.settings_scrolledwindow = wx.lib.scrolledpanel.ScrolledPanel(self.main_splitter)
        self.settings_scrolledwindow.SetupScrolling()
        self.settings_scrolledwindow.SetAutoLayout(1)
        self.settings_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_scrolledwindow.SetSizer(self.settings_sizer)

        # ---------------------------------------------

        self.settings_item_panel = wx.Panel(self.settings_scrolledwindow, style=wx.BORDER_STATIC)
        self.settings_item_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_item_panel.SetSizer(self.settings_item_sizer)

        self.settings_sizer.Add(self.settings_item_panel, 1, wx.EXPAND)
        # ---------------------------------------------

        self.main_splitter.SplitVertically(self.settings_items_treectrl, self.settings_scrolledwindow, 200)
        self.sizer.Add(self.main_splitter, 1, wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND)
        # ------------------------------

        self.buttons_panel = wx.Panel(self.panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.ok_button = wx.Button(self.buttons_panel, label='ОК', size=(75, -1))
        self.ok_button.Bind(wx.EVT_BUTTON, self.apply_close)
        self.buttons_sizer.Add(self.ok_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.cancel_button = wx.Button(self.buttons_panel, label='Отмена', size=(75, -1))
        self.cancel_button.Bind(wx.EVT_BUTTON, self.close)
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.apply_button = wx.Button(self.buttons_panel, label='Принять', size=(75, -1))
        self.apply_button.Bind(wx.EVT_BUTTON, self.apply)
        self.buttons_sizer.Add(self.apply_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.sizer.Add(self.buttons_panel, 0, wx.ALIGN_RIGHT)
        # ---------------

        self.Layout()
