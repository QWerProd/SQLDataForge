import os
import wx
import sqlite3

from data_controller import DataController as DC
from connections.udb_conn.new_conn import NewConnection
from app_parameters import APP_TEXT_LABELS, APPLICATION_PATH


class ConnectionViewer(wx.Frame):
    databases = list
    db_info = list

    def set_databases(self):
        for database in self.databases:
            if database[2].startswith('data') or database[2].endswith('SQLDataForge/data'):
                item = self.treectrl_databases.AppendItem(self.local_root, database[0])
            else:
                item = self.treectrl_databases.AppendItem(self.global_root, database[0])
            if database[4] == 'Y':
                self.treectrl_databases.SetItemImage(item, self.database_image)
            else:
                self.treectrl_databases.SetItemImage(item, self.invalid_db_image)

    def opening(self, event):
        item = event.GetItem()
        self.treectrl_databases.SetItemImage(item, self.opened_root)

    def on_activated(self, event):
        # Получаем выделенный элемент
        get_item = event.GetItem()
        activated = self.treectrl_databases.GetItemText(get_item)
        if not activated.endswith('.db'):
            return

        self.set_values(activated)

    def set_values(self, db_name: str):
        # Ищем выбранную пБД среди остальных
        for database in self.databases:
            if db_name in database:
                self.db_info = database
                break

        # Разблокируем текстовые поля и кнопки
        self.db_name_textctrl.Enable()
        self.db_field_name_textctrl.Enable()
        self.db_valid_textctrl.Enable()
        self.db_desc_textctrl.Enable()
        self.save_button.Enable()
        self.save_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.save_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))

        # Ставим значения
        self.db_name_textctrl.SetValue(self.db_info[0])
        if self.db_info[1] is None or self.db_info[1] == '':
            self.db_field_name_textctrl.SetHint(self.db_info[0])
            self.db_field_name_textctrl.Clear()
        else:
            self.db_field_name_textctrl.SetValue(self.db_info[1])
        self.db_valid_textctrl.SetValue(self.db_info[4])
        if self.db_info[4] == 'Y':
            self.db_valid_textctrl.SetBackgroundColour(wx.Colour(144, 249, 173))
        else:
            self.db_valid_textctrl.SetBackgroundColour(wx.Colour(250, 145, 145))
        self.db_path_textctrl.SetValue(self.db_info[2])
        if self.db_info[3] is None or self.db_info[3] == '':
            self.db_desc_textctrl.SetHint(APP_TEXT_LABELS['CONNECTION_VIEWER.DB_DESC.HINT'])
            self.db_desc_textctrl.Clear()
        else:
            self.db_desc_textctrl.SetValue(self.db_info[3])

    def refresh(self, event=wx.EVT_BUTTON, block=True):
        self.databases = DC.GetDatabases(False)
        self.treectrl_databases.DeleteAllItems()
        root = self.treectrl_databases.AddRoot('')
        self.local_root = self.treectrl_databases.AppendItem(root, APP_TEXT_LABELS['CONNECTION_VIEWER.DB_TREE.LOCAL_UDB'])
        self.treectrl_databases.SetItemImage(self.local_root, self.closed_root)
        self.global_root = self.treectrl_databases.AppendItem(root, APP_TEXT_LABELS['CONNECTION_VIEWER.DB_TREE.GLOBAL_UDB'])
        self.treectrl_databases.SetItemImage(self.global_root, self.closed_root)
        self.set_databases()

        if block:
            self.db_name_textctrl.Clear()
            self.db_name_textctrl.Disable()
            self.db_field_name_textctrl.Clear()
            self.db_field_name_textctrl.Disable()
            self.db_valid_textctrl.Clear()
            self.db_valid_textctrl.Disable()
            self.db_path_textctrl.Clear()
            self.db_desc_textctrl.Clear()
            self.db_desc_textctrl.Disable()
            self.save_button.Disable()
            self.save_button.Unbind(wx.EVT_ENTER_WINDOW)

    def new_connection(self, event):
        with NewConnection(self) as new_conn:
            new_conn.ShowModal()

        self.refresh(block=False)

    def drop_connection(self, event):
        item = self.treectrl_databases.GetSelection()
        root_item = self.treectrl_databases.GetItemParent(item)
        root_text = self.treectrl_databases.GetItemText(root_item)
        is_valid_text = self.db_valid_textctrl.GetValue()
        if is_valid_text == 'Y':
            if root_text == APP_TEXT_LABELS['CONNECTION_VIEWER.DB_TREE.LOCAL_UDB']:
                return wx.MessageBox(APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.MESSAGE'],
                                     APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.CAPTION'],
                                     wx.OK | wx.ICON_WARNING)
            elif len(self.databases) <= 1:
                return wx.MessageBox(APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.DROP_SINGLE_CONNECTION.MESSAGE'],
                                     APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.CAPTION'],
                                     wx.OK | wx.ICON_WARNING)
            with wx.Dialog(APP_TEXT_LABELS['TEST_DB_VIEWER.DELETE_APPROVE.MESSAGE'],
                           APP_TEXT_LABELS['TEST_DB_VIEWER.DELETE_APPROVE.CAPTION'],
                           wx.YES_NO | wx.ICON_WARNING) as dlg:
                if dlg.ShowModal() == wx.NO_ID:
                    return

        database = self.treectrl_databases.GetItemText(item)

        # Удаляем сведения о пБД
        app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))
        cursor = app_conn.cursor()
        try:
            cursor.execute(f"""DELETE FROM t_databases
                               WHERE dbname = "{database}";""")
            app_conn.commit()

            self.refresh()
        except sqlite3.Error as e:
            app_conn.rollback()
            wx.MessageBox(str(e) + '\n' + e.sqlite_errorname,
                          APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.CAPTION'])
        finally:
            cursor.close()
            app_conn.close()

        # Удаляем файл пБД, если она локальная
        if root_text == APP_TEXT_LABELS['CONNECTION_VIEWER.DB_TREE.LOCAL_UDB']:
            try:
                os.remove('data/' + database)
            except:
                pass

        self.refresh()

    def save_changes(self, event):
        app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))
        cursor = app_conn.cursor()
        try:
            rowid = cursor.execute(f"""SELECT id FROM t_databases 
                                       WHERE path = '{self.db_info[2]}' AND dbname = '{self.db_info[0]}';""").fetchone()[0]

            # Получаем значения из полей
            dbname = self.db_name_textctrl.GetValue()
            if not dbname.endswith('.db'):
                dbname += '.db'
            db_field_name = self.db_field_name_textctrl.GetValue()
            db_desc = self.db_desc_textctrl.GetValue()

            # Переименовываем файл если есть изменения в имени файла
            if self.db_info[0] != dbname:
                os.rename(os.path.join(self.db_info[2], self.db_info[0]), os.path.join(self.db_info[2], dbname))

            # Изменение данных
            cursor.execute(f"""UPDATE t_databases
                               SET dbname = "{dbname}",
                                   field_name = "{db_field_name}",
                                   description = "{db_desc}"
                               WHERE id = {int(rowid)};""")
            app_conn.commit()
            wx.MessageBox(f'{dbname}:\n' + APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.SUCCESS_SAVE_CHANGES.MESSAGE'],
                          APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.SUCCESS_SAVE_CHANGES.CAPTION'], wx.OK | wx.ICON_INFORMATION)

            self.refresh(block=False)

        except sqlite3.Error as e:
            app_conn.rollback()
            wx.MessageBox(str(e) + '\n' + e.sqlite_errorname, APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.ERROR_SAVE_CHANGES.CAPTION'])
        finally:
            cursor.close()
            app_conn.close()

    def close(self, event):
        if self.db_name_textctrl.IsEnabled():
            result = wx.MessageBox(APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.CLOSE_ATTENTION.MESSAGE'],
                                   APP_TEXT_LABELS['CONNECTION_VIEWER.MESSAGE_BOX.CLOSE_ATTENTION.CAPTION'],
                                   wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if result == wx.OK:
                self.Destroy()
            else:
                return
        else:
            self.Destroy()

    def __init__(self, db_name: str = None):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['CONNECTION_VIEWER.TITLE'], size=(500, 550),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.FRAME_NO_TASKBAR)
        self.SetMinSize((500, 550))
        self.SetMaxSize((500, 550))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))

        self.databases = DC.GetDatabases(False)

        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        # ------------

        div_hor_panel = wx.Panel(self.main_panel, size=(-1, 250))
        div_hor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_hor_panel.SetSizer(div_hor_sizer)

        # Дерево
        self.treectrl_databases = wx.TreeCtrl(div_hor_panel, style=wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT | wx.TR_HAS_BUTTONS)
        div_hor_sizer.Add(self.treectrl_databases, 1, wx.LEFT | wx.EXPAND | wx.TOP, 5)

        self.image_items = wx.ImageList(16, 16)
        self.closed_root = self.image_items.Add(wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/book 1.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.opened_root = self.image_items.Add(wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/book.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.database_image = self.image_items.Add(wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/database.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.invalid_db_image = self.image_items.Add(wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/delete database.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.treectrl_databases.AssignImageList(self.image_items)

        root = self.treectrl_databases.AddRoot('')
        self.local_root = self.treectrl_databases.AppendItem(root, APP_TEXT_LABELS['CONNECTION_VIEWER.DB_TREE.LOCAL_UDB'])
        self.treectrl_databases.SetItemImage(self.local_root, self.closed_root)
        self.global_root = self.treectrl_databases.AppendItem(root, APP_TEXT_LABELS['CONNECTION_VIEWER.DB_TREE.GLOBAL_UDB'])
        self.treectrl_databases.SetItemImage(self.global_root, self.closed_root)

        self.set_databases()
        self.treectrl_databases.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.opening)
        self.treectrl_databases.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_activated)

        # -------------------------------

        buttons_panel = wx.Panel(div_hor_panel)
        buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        buttons_panel.SetSizer(buttons_sizer)

        self.refresh_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                              bitmap=wx.BitmapBundle(wx.Bitmap(os.path.join(APPLICATION_PATH, 'img/16x16/update.png'))))
        self.refresh_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.refresh_button.Bind(wx.EVT_BUTTON, self.refresh)
        self.refresh_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.refresh_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        buttons_sizer.Add(self.refresh_button, 0, wx.BOTTOM, 5)

        self.add_database_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                                   bitmap=wx.BitmapBundle(wx.Bitmap(os.path.join(APPLICATION_PATH, 'img/16x16/database  add.png'))))
        self.add_database_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.add_database_button.Bind(wx.EVT_BUTTON, self.new_connection)
        self.add_database_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.add_database_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        buttons_sizer.Add(self.add_database_button, 0, wx.BOTTOM, 5)

        self.delete_database_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                                      bitmap=wx.BitmapBundle(wx.Bitmap(os.path.join(APPLICATION_PATH, 'img/16x16/database delete.png'))))
        self.delete_database_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.delete_database_button.Bind(wx.EVT_BUTTON, self.drop_connection)
        self.delete_database_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.delete_database_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        buttons_sizer.Add(self.delete_database_button, 0, wx.BOTTOM, 5)

        div_hor_sizer.Add(buttons_panel, 0, wx.ALL, 5)
        # -------------------------------

        self.main_sizer.Add(div_hor_panel, 0, wx.EXPAND, 0)
        # ------------

        info_panel = wx.Panel(self.main_panel)
        info_staticbox = wx.StaticBox(info_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_INFO'])
        info_staticsizer = wx.StaticBoxSizer(info_staticbox, wx.VERTICAL)
        info_panel.SetSizer(info_staticsizer)

        # -------------------------------

        self.main_info_panel = wx.Panel(info_staticbox)
        self.main_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_info_panel.SetSizer(self.main_info_sizer)

        self.db_name_textctrl = wx.TextCtrl(self.main_info_panel)
        self.db_name_textctrl.Disable()
        self.main_info_sizer.AddMany([(wx.StaticText(self.main_info_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_NAME'],
                                                     size=(50, -1)), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                                      (self.db_name_textctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])

        self.db_field_name_textctrl = wx.TextCtrl(self.main_info_panel)
        self.db_field_name_textctrl.Disable()
        self.main_info_sizer.AddMany([(wx.StaticText(self.main_info_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_ALIAS']),
                                       0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                                      (self.db_field_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
        self.db_valid_textctrl = wx.TextCtrl(self.main_info_panel, size=(25, -1), style=wx.TE_READONLY)
        self.db_valid_textctrl.Disable()
        self.main_info_sizer.Add(self.db_valid_textctrl, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        info_staticsizer.Add(self.main_info_panel, 0, wx.ALL | wx.EXPAND)
        info_staticsizer.Add(wx.StaticLine(info_staticbox), 0, wx.EXPAND | wx.ALL, 5)
        # -------------------------------

        self.path_panel = wx.Panel(info_staticbox)
        self.path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.path_panel.SetSizer(self.path_sizer)

        self.db_path_textctrl = wx.TextCtrl(self.path_panel)
        self.db_path_textctrl.Disable()
        self.path_sizer.AddMany([(wx.StaticText(self.path_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_PATH'],
                                                size=(50, -1)), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                                 (self.db_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])

        info_staticsizer.Add(self.path_panel, 0, wx.ALL | wx.EXPAND)
        info_staticsizer.Add(wx.StaticLine(info_staticbox), 0, wx.EXPAND | wx.ALL, 5)
        # -------------------------------

        self.desc_panel = wx.Panel(info_staticbox)
        self.desc_sizer = wx.BoxSizer(wx.VERTICAL)
        self.desc_panel.SetSizer(self.desc_sizer)

        self.db_desc_textctrl = wx.TextCtrl(self.desc_panel, style=wx.TE_MULTILINE)
        self.db_desc_textctrl.Disable()
        self.desc_sizer.AddMany([(wx.StaticText(self.desc_panel, label=APP_TEXT_LABELS['CONNECTION_VIEWER.DB_DESC']),
                                  0, wx.TOP | wx.LEFT, 5),
                                 (self.db_desc_textctrl, 1, wx.ALL | wx.EXPAND, 5)])

        info_staticsizer.Add(self.desc_panel, 1, wx.ALL | wx.EXPAND)
        # -------------------------------

        self.main_sizer.Add(info_panel, 1, wx.ALL | wx.EXPAND, 5)
        # ------------

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

        self.main_sizer.Add(self.buttons_panel, 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)
        # ------------

        if db_name is not None:
            self.set_values(db_name)

        self.main_panel.Layout()
