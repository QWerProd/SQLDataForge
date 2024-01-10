import sqlite3

import wx.stc
import wx.lib.scrolledpanel

from app.tools.settings_entries import *
from app.app_parameters import APP_PARAMETERS, APP_TEXT_LABELS


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
        id_parents = curs.execute(f"""SELECT si.id, lt.text
                                      FROM t_settings_items as si,
                                           t_lang_text as lt
                                      WHERE si.id_fk IS NULL
                                      AND si.is_valid = 'Y'
                                      AND si.sett_label = lt.label
                                      AND lt.lang = '{APP_PARAMETERS['APP_LANGUAGE']}'
                                      ORDER BY si.id;""").fetchall()

        for parent in id_parents:
            self.sett_items[(parent[0], parent[1])] = []
            self.parent_items.append(parent[1])
            id_childrens = curs.execute(f"""SELECT si.id, lt.text
                                            FROM t_settings_items as si,
                                                 t_lang_text as lt
                                            WHERE si.id_fk = {parent[0]}
                                            AND si.is_valid = 'Y'
                                            AND si.sett_label = lt.label
                                            AND lt.lang = '{APP_PARAMETERS['APP_LANGUAGE']}'
                                            ORDER BY si.id;""").fetchall()
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
            entries = curs.execute(f"""SELECT p.param_name, sip.entry_type, lt.text, sip.entry_choices, p.param_value, lt2.text
                                       FROM t_settings_items_params as sip
                                       JOIN t_settings_items as si ON sip.id_parent = si.id
                                       LEFT JOIN t_params as p ON sip.id_param = p.id
                                       LEFT JOIN t_lang_text as lt ON sip.entry_label = lt.label
                                       LEFT JOIN t_lang_text as lt2 ON sip.entry_label_choices = lt2.label
                                       WHERE si.sett_label = (SELECT label FROM t_lang_text WHERE text = '{menu_name}' AND label LIKE 'APP.%')
                                       AND   sip.is_valid = 'Y'
                                       AND   si.is_valid = 'Y'
                                       AND   (lt.lang = '{APP_PARAMETERS['APP_LANGUAGE']}' OR lt.lang IS NULL)
                                       AND   (lt2.lang = '{APP_PARAMETERS['APP_LANGUAGE']}' OR lt2.lang IS NULL)
                                       ORDER BY sip.posid;""").fetchall()

            for entry in entries:
                menu_entry_panel = None
                if entry[1] == 'CheckboxPoint':
                    menu_entry_panel = CheckboxPoint(self.settings_item_panel, entry[2])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL | wx.EXPAND, 2)
                elif entry[1] == 'RadioSelect':
                    menu_entry_panel = RadioSelect(self.settings_item_panel, entry[2], entry[3])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL, 2)
                elif entry[1] == 'SelectorBox':
                    menu_entry_panel = SelectorBox(self.settings_item_panel, entry[2], entry[3].split(':'), entry[5].split(':'))
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
                    menu_entry_panel = CodeRedactor(self.settings_item_panel, entry[3])
                    self.settings_item_sizer.Add(menu_entry_panel, 1, wx.ALL | wx.EXPAND, 5)
                elif entry[1] == 'TableSystemColumns':
                    title_columns = entry[2].split(':')
                    curs = self.app_conn.cursor()
                    # Подстановка текущего значения языка приложения
                    query = entry[3].replace('$0', APP_PARAMETERS['APP_LANGUAGE'])

                    # Подстановка остальных значений
                    if entry[5] is not None:
                        items = str(entry[5]).split(':')
                        for i in range(len(items)):
                            query = query.replace(f'${i + 1}', APP_PARAMETERS[items[i]])

                    data_rows = curs.execute(query).fetchall()
                    menu_entry_panel = TableSystemColumns(self.settings_item_panel, title_columns, data_rows)
                    self.settings_item_sizer.Add(menu_entry_panel, 1, wx.ALL | wx.EXPAND, 5)
                elif entry[1] == 'MaskedTextEntry':
                    menu_entry_panel = MaskedTextEntry(self.settings_item_panel, entry[2])
                    self.settings_item_sizer.Add(menu_entry_panel, 0, wx.ALL | wx.EXPAND, 2)

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
            if param_entry[0] is not None and type(param_entry[1]) not in (TableSystemColumns, ):
                param_value = param_entry[1].param
                if self.prev_page is not None and APP_PARAMETERS[param_entry[0]] != str(param_value):
                    self.changed_params[self.prev_page][param_entry[0]] = str(param_value)
                    self.changed_params_journal[self.prev_page][param_entry[0]] = str(param_value)
                elif APP_PARAMETERS[param_entry[0]] != str(param_value):
                    self.changed_params[menu_item][param_entry[0]] = str(param_value)
                    self.changed_params_journal[menu_item][param_entry[0]] = str(param_value)
            elif type(param_entry[1]) in (TableSystemColumns, ):
                param_values = param_entry[1].get_params()
                if self.prev_page is not None:
                    self.changed_params[self.prev_page] = param_values
                    self.changed_params_journal[self.prev_page] = param_values
                else:
                    self.changed_params[menu_item] = param_values
                    self.changed_params_journal[menu_item] = param_values

        self.prev_page = menu_item

    def close(self, event):
        for values in self.changed_params.values():
            if len(values.keys()) > 0:
                dlg = wx.MessageBox(APP_TEXT_LABELS['SETTINGS.MESSAGE_BOX.CLOSE.ALL_CLEAR'],
                                    APP_TEXT_LABELS['MESSAGE_BOX.CAPTION_APPROVE'],
                                    wx.YES_NO | wx.NO_DEFAULT)
                if dlg == wx.YES:
                    self.EndModal(0)
                else:
                    return
            else:
                continue
        self.EndModal(0)

    def apply(self, event):
        ret_code = self.change_settings()
        if ret_code == 2:
            if self.restart_offer():
                self.EndModal(ret_code)
        self.set_setting_page(menu_name=self.prev_page)

    def apply_close(self, event):
        ret_code = self.change_settings()
        if ret_code == 2:
            if not self.restart_offer():
                ret_code -= 1
        self.EndModal(ret_code)

    def restart_offer(self):
        """Возвращает True/False как ответ, необходима ли перезагрузка приложения."""
        dlg = wx.MessageDialog(self,
                               APP_TEXT_LABELS['SETTINGS.RESTART_FOR_APPLY_CHANGES.MESSAGE'],
                               APP_TEXT_LABELS['SETTINGS.RESTART_FOR_APPLY_CHANGES.CAPTION'],
                               wx.YES_NO | wx.YES_DEFAULT)
        result = True if dlg.ShowModal() == wx.ID_YES else False
        return result

    def change_settings(self) -> int:
        curs = self.app_conn.cursor()
        self.set_params()
        changed_params = []
        for entry_page_name, entry_page_params in self.changed_params.items():
            for entry_name, entry_value in entry_page_params.items():
                curs.execute(f"""UPDATE t_params
                                 SET    param_value = '{entry_value}'
                                 WHERE  param_name = '{entry_name}';""")
                self.app_conn.commit()
                APP_PARAMETERS[entry_name] = entry_value
                changed_params.append(entry_name)
        self.changed_params.clear()
        try:
            ret_code = int(curs.execute(f"""SELECT MAX(p.update_layout)
                                        FROM t_params p
                                        WHERE p.param_name IN ('{"','".join(changed_params)}');""").fetchone()[0])
        except TypeError:
            ret_code = 0
        curs.close()
        return ret_code

    def __init__(self, parent: wx.Frame):
        super().__init__(parent, title=APP_TEXT_LABELS['SETTINGS.TITLE'], size=(700, 500),
                         style=wx.CAPTION | wx.CLOSE_BOX)
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))
        self.Bind(wx.EVT_CLOSE, self.close)
        self.app_conn = sqlite3.connect('app/app.db')
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

        self.ok_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.OK'], size=(75, -1))
        self.ok_button.Bind(wx.EVT_BUTTON, self.apply_close)
        self.ok_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.ok_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.ok_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.cancel_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.CANCEL'], size=(75, -1))
        self.cancel_button.Bind(wx.EVT_BUTTON, self.close)
        self.cancel_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.cancel_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.apply_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.APPLY'], size=(75, -1))
        self.apply_button.Bind(wx.EVT_BUTTON, self.apply)
        self.apply_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.apply_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.buttons_sizer.Add(self.apply_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.sizer.Add(self.buttons_panel, 0, wx.ALIGN_RIGHT)
        # ---------------

        self.Layout()
