import os
import wx
import sqlite3

from data_controller import DataController as DC
from conn_frames.new_conn import NewConnection


class ConnectionViewer(wx.Frame):
    connect = sqlite3.Connection
    databases = list
    db_info = list

    def set_databases(self):
        for database in self.databases:
            if database[2].startswith('data') or database[2].endswith('SQLDataForge/data'):
                item = self.treectrl_databases.AppendItem(self.local_root, database[0])
                self.treectrl_databases.SetItemImage(item, self.database_image)
            else:
                item = self.treectrl_databases.AppendItem(self.global_root, database[0])
                self.treectrl_databases.SetItemImage(item, self.database_image)

    def opening(self, event):
        item = event.GetItem()
        self.treectrl_databases.SetItemImage(item, self.opened_root)

    def on_activated(self, event):
        # Получаем выделенный элемент
        get_item = event.GetItem()
        activated = self.treectrl_databases.GetItemText(get_item)
        if not activated.endswith('.db'):
            return

        # Ищем выбранную пБД среди остальных
        for database in self.databases:
            if activated in database:
                self.db_info = database
                break

        # Разблокируем текстовые поля и кнопки
        self.db_name_textctrl.Enable()
        self.db_field_name_textctrl.Enable()
        self.db_desc_textctrl.Enable()
        self.save_button.Enable()

        # Ставим значения
        self.db_name_textctrl.SetValue(self.db_info[0])
        if self.db_info[1] is None or self.db_info[1] == '':
            self.db_field_name_textctrl.SetHint(self.db_info[0])
        else:
            self.db_field_name_textctrl.SetValue(self.db_info[1])
        self.db_path_textctrl.SetValue(self.db_info[2])
        if self.db_info[3] is None or self.db_info[3] == '':
            self.db_desc_textctrl.SetHint('Описание отсутствует...')
        else:
            self.db_desc_textctrl.SetValue(self.db_info[3])

    def refresh(self, event=wx.EVT_BUTTON):
        self.databases = DC.GetDatabases(False)
        self.treectrl_databases.DeleteAllItems()
        root = self.treectrl_databases.AddRoot('')
        self.local_root = self.treectrl_databases.AppendItem(root, 'локальные пБД')
        self.treectrl_databases.SetItemImage(self.local_root, self.closed_root)
        self.global_root = self.treectrl_databases.AppendItem(root, 'внешние пБД')
        self.treectrl_databases.SetItemImage(self.global_root, self.closed_root)
        self.set_databases()

        self.db_name_textctrl.Clear()
        self.db_name_textctrl.Disable()
        self.db_field_name_textctrl.Clear()
        self.db_field_name_textctrl.Disable()
        self.db_path_textctrl.Clear()
        self.db_desc_textctrl.Clear()
        self.db_desc_textctrl.Disable()
        self.save_button.Disable()

    def new_connection(self, event):
        new_conn = NewConnection(self.connect)
        new_conn.Show()
        new_conn.SetFocus()

    def drop_connection(self, event):
        item = self.treectrl_databases.GetSelection()
        root_item = self.treectrl_databases.GetItemParent(item)
        root_text = self.treectrl_databases.GetItemText(root_item)
        if root_text == 'локальные пБД':
            return wx.MessageBox('Вы не можете удалить пБД из локального репозитория', 'Ошибка удаления',
                                 wx.OK | wx.ICON_WARNING)
        elif len(self.databases) <= 1:
            return wx.MessageBox('Должна остаться хотя бы одна пБД!', 'Ошибка удаления',
                                 wx.OK | wx.ICON_WARNING)

        database = self.treectrl_databases.GetItemText(item)
        try:
            cursor = self.connect.cursor()
            cursor.execute(f"""DELETE FROM t_databases
                               WHERE dbname = "{database}";""")
            self.connect.commit()
            cursor.close()

            self.refresh()
        except sqlite3.Error as e:
            self.connect.rollback()
            wx.MessageBox(str(e) + '\n' + e.sqlite_errorname, 'Ошибка удаления')

    def save_changes(self, event):
        try:
            cursor = self.connect.cursor()
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
                os.rename(self.db_info[2] + '/' + self.db_info[0], self.db_info[2] + '/' + dbname)

            # Изменение данных
            cursor.execute(f"""UPDATE t_databases
                               SET dbname = "{dbname}",
                                   field_name = "{db_field_name}",
                                   description = "{db_desc}"
                               WHERE id = {int(rowid)};""")
            self.connect.commit()
            wx.MessageBox(f'пБД {dbname} успешно изменена!', 'Успешное изменение', wx.OK | wx.ICON_INFORMATION)
        except sqlite3.Error as e:
            self.connect.rollback()
            wx.MessageBox(str(e) + '\n' + e.sqlite_errorname, 'Ошибка сохранения')

    def close(self, event):
        if self.db_name_textctrl.IsEnabled():
            result = wx.MessageBox('Несохраненные данные будут удалены!',
                                   'Вы уверены?', wx.OK | wx.CANCEL | wx.ICON_WARNING)
            if result == wx.OK:
                self.Destroy()
            else:
                return
        else:
            self.Destroy()

    def __init__(self, conn: sqlite3.Connection):
        wx.Frame.__init__(self, None, title="Доступные пБД", size=(500, 550),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.FRAME_TOOL_WINDOW | wx.FRAME_NO_TASKBAR)
        self.SetMinSize((500, 550))
        self.SetMaxSize((500, 550))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))

        self.connect = conn
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
        self.closed_root = self.image_items.Add(wx.Image('img/16x16/book 1.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.opened_root = self.image_items.Add(wx.Image('img/16x16/book.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.database_image = self.image_items.Add(wx.Image('img/16x16/database.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.treectrl_databases.AssignImageList(self.image_items)

        root = self.treectrl_databases.AddRoot('')
        self.local_root = self.treectrl_databases.AppendItem(root, 'локальные пБД')
        self.treectrl_databases.SetItemImage(self.local_root, self.closed_root)
        self.global_root = self.treectrl_databases.AppendItem(root, 'внешние пБД')
        self.treectrl_databases.SetItemImage(self.global_root, self.closed_root)

        self.set_databases()
        self.treectrl_databases.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.opening)
        self.treectrl_databases.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_activated)

        # -------------------------------

        buttons_panel = wx.Panel(div_hor_panel)
        buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        buttons_panel.SetSizer(buttons_sizer)

        self.refresh_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                              bitmap=wx.BitmapBundle(wx.Bitmap('img/16x16/update.png')))
        self.refresh_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.refresh_button.Bind(wx.EVT_BUTTON, self.refresh)
        buttons_sizer.Add(self.refresh_button, 0, wx.BOTTOM, 5)

        self.add_database_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                                   bitmap=wx.BitmapBundle(wx.Bitmap('img/16x16/database  add.png')))
        self.add_database_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.add_database_button.Bind(wx.EVT_BUTTON, self.new_connection)
        buttons_sizer.Add(self.add_database_button, 0, wx.BOTTOM, 5)

        self.delete_database_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                                      bitmap=wx.BitmapBundle(wx.Bitmap('img/16x16/delete database.png')))
        self.delete_database_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.delete_database_button.Bind(wx.EVT_BUTTON, self.drop_connection)
        buttons_sizer.Add(self.delete_database_button, 0, wx.BOTTOM, 5)

        div_hor_sizer.Add(buttons_panel, 0, wx.ALL, 5)
        # -------------------------------

        self.main_sizer.Add(div_hor_panel, 0, wx.EXPAND, 0)
        # ------------

        info_panel = wx.Panel(self.main_panel)
        info_staticbox = wx.StaticBox(info_panel, label='Сведения о пБД')
        info_staticsizer = wx.StaticBoxSizer(info_staticbox, wx.VERTICAL)
        info_panel.SetSizer(info_staticsizer)

        # -------------------------------

        self.main_info_panel = wx.Panel(info_staticbox)
        self.main_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_info_panel.SetSizer(self.main_info_sizer)

        self.db_name_textctrl = wx.TextCtrl(self.main_info_panel)
        self.db_name_textctrl.Disable()
        self.main_info_sizer.AddMany([(wx.StaticText(self.main_info_panel, label='Имя:', size=(50, -1)), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                                      (self.db_name_textctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])

        self.db_field_name_textctrl = wx.TextCtrl(self.main_info_panel)
        self.db_field_name_textctrl.Disable()
        self.main_info_sizer.AddMany([(wx.StaticText(self.main_info_panel, label='Псевдоним:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                                      (self.db_field_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])

        info_staticsizer.Add(self.main_info_panel, 0, wx.ALL | wx.EXPAND)
        info_staticsizer.Add(wx.StaticLine(info_staticbox), 0, wx.EXPAND | wx.ALL, 5)
        # -------------------------------

        self.path_panel = wx.Panel(info_staticbox)
        self.path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.path_panel.SetSizer(self.path_sizer)

        self.db_path_textctrl = wx.TextCtrl(self.path_panel)
        self.db_path_textctrl.Disable()
        self.path_sizer.AddMany([(wx.StaticText(self.path_panel, label='Путь:', size=(50, -1)), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5),
                                 (self.db_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])

        info_staticsizer.Add(self.path_panel, 0, wx.ALL | wx.EXPAND)
        info_staticsizer.Add(wx.StaticLine(info_staticbox), 0, wx.EXPAND | wx.ALL, 5)
        # -------------------------------

        self.desc_panel = wx.Panel(info_staticbox)
        self.desc_sizer = wx.BoxSizer(wx.VERTICAL)
        self.desc_panel.SetSizer(self.desc_sizer)

        self.db_desc_textctrl = wx.TextCtrl(self.desc_panel, style=wx.TE_MULTILINE)
        self.db_desc_textctrl.Disable()
        self.desc_sizer.AddMany([(wx.StaticText(self.desc_panel, label='Описание:'), 0, wx.TOP | wx.LEFT, 5),
                                 (self.db_desc_textctrl, 1, wx.ALL | wx.EXPAND, 5)])

        info_staticsizer.Add(self.desc_panel, 1, wx.ALL | wx.EXPAND)
        # -------------------------------

        self.main_sizer.Add(info_panel, 1, wx.ALL | wx.EXPAND, 5)
        # ------------

        self.buttons_panel = wx.Panel(self.main_panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)
        self.buttons_sizer.Add(320, 0, 0)

        self.close_button = wx.Button(self.buttons_panel, label='Закрыть', size=(75, -1))
        self.close_button.Bind(wx.EVT_BUTTON, self.close)
        self.buttons_sizer.Add(self.close_button, 0, wx.ALL, 5)

        self.save_button = wx.Button(self.buttons_panel, label='Сохранить', size=(75, -1))
        self.save_button.Disable()
        self.save_button.Bind(wx.EVT_BUTTON, self.save_changes)
        self.buttons_sizer.Add(self.save_button, 0, wx.ALL, 5)

        self.main_sizer.Add(self.buttons_panel, 0, wx.BOTTOM | wx.EXPAND, 5)
        # ------------

        self.main_panel.Layout()
