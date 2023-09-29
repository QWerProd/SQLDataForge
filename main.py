import wx
import wx.stc
import sqlite3

from datetime import datetime
from data_controller import DataController
from sql_generator import SQLGenerator
from error_catcher import ErrorCatcher

app_conn = sqlite3.connect('app/app.db')
catcher = ErrorCatcher()


class MainFrame(wx.Frame):
    tree_items = {}
    added_items = []
    added_item_text = []
    all_tables = {}

    # Параметры страницы "Таблица"
    is_create_table = False
    is_id_column = False

    # Параметры состояния
    is_generated = False
    is_saved = False
    query_status = "Ожидание"

    # TODO: Подготовка к переходу на "таблицу" вместо текстовой области
    #       Редактировать метод, чтобы он добавлял несколько элементов и записывал
    def OnActivated(self, evt):
        get_item = evt.GetItem()
        activated = self.treectrl_databases.GetItemText(get_item)
        if activated.endswith('.db'):
            return 0
        else:
            add_act = ""
            get_parent = self.treectrl_databases.GetItemParent(get_item)
            parent_name = self.treectrl_databases.GetItemText(get_parent)

            for key in self.all_tables:
                if key != parent_name:
                    continue
                else:
                    for item in self.all_tables[key]:
                        if item.find(activated) != -1:
                            add_act = item

            if len(self.added_items) <= 0:
                self.added_items.append(add_act)
                self.added_item_text.append(activated)
                self.treectrl_databases.SetItemBold(get_item, True)
            else:
                is_removed = False
                for item in self.added_items:
                    if activated in item:
                        self.added_items.remove(add_act)
                        self.added_item_text.remove(activated)
                        self.treectrl_databases.SetItemBold(get_item, False)
                        is_removed = True
                        break
                if not is_removed:
                    self.added_items.append(add_act)
                    self.added_item_text.append(activated)
                    self.treectrl_databases.SetItemBold(get_item, True)
            self.textctrl_used_tables.SetValue(', '.join(self.added_item_text))

    def Generate(self, event):
        start_generate_time = datetime.now()
        table_info = {}
        table_name = self.textctrl_table_name.GetValue()
        rows_count = self.textctrl_rows_count.GetValue()

        self.query_status = "Генерация запроса..."
        self.statusbar.SetStatusText(self.query_status, 0)

        if len(self.added_items) == 0:
            self.query_status = catcher.error_message('E003')
            self.statusbar.SetStatusText(self.query_status, 0)
        elif table_name == '':
            self.query_status = catcher.error_message('E004')
            self.statusbar.SetStatusText(self.query_status, 0)
        elif rows_count == '':
            self.query_status = catcher.error_message('E005')
            self.statusbar.SetStatusText(self.query_status, 0)
        else:
            try:
                rows_count = int(rows_count)
                if rows_count <= 0:
                    return catcher.error_message('E006')

                temp = {'is_id_create': False}
                if self.is_create_table:
                    id_create = self.id_column_checkbox.GetValue()
                    temp['is_id_create'] = id_create
                    if self.is_id_column:
                        increment = self.textctrl_increment_start.GetValue()
                        temp['increment_start'] = increment
                table_info[table_name] = temp

                start_build_time = datetime.now()
                builder = SQLGenerator(app_conn, table_info, rows_count, self.added_items)
                query = ''
                query += builder.BuildQuery(self.is_create_table)
                build_time = datetime.now() - start_build_time
                self.textctrl_sql.SetValue(query)
                self.is_generated = True
                self.is_saved = False
                self.query_status = "Готово"
                self.statusbar.SetStatusText(self.query_status, 0)
                generate_time = datetime.now() - start_generate_time

                build_time = round(build_time.total_seconds(), 4)
                generate_time = round(generate_time.total_seconds(), 2)
                self.statusbar.SetStatusText("Сгенерировано за: " + str(build_time) + " с., всего: " + str(generate_time) + " с.", 2)

            except ValueError:
                self.query_status = catcher.error_message('E010')
                self.statusbar.SetStatusText(self.query_status, 0)

    def SaveScript(self, is_new=True):
        sql = self.textctrl_sql.GetValue()
        if sql == "":
            self.query_status = catcher.error_message('E001')
            self.statusbar.SetStatusText(self.query_status, 0)
        else:
            with wx.FileDialog(self, "Сохранить как...", wildcard="Файл SQL(*.sql)|*.sql", style=wx.FD_SAVE) as file_dialog:
                if file_dialog.ShowModal() == wx.CANCEL:
                    return

                file_path = file_dialog.GetPath()
                file_name = file_dialog.GetName()

                if not file_path.endswith('.sql'):
                    file_name += '.sql'
                    file_path += '.sql'

                with open(file_path, mode='w', encoding="utf-8") as reader:
                    reader.write(sql)
                wx.MessageBox("Файл " + file_name + " сохранен в " + file_path, "Сохранено",
                              wx.ICON_INFORMATION | wx.OK, self)
            self.is_saved = True
            self.query_status = "Сохранено"
            self.statusbar.SetStatusText(self.query_status, 0)

    def OnClose(self, event):
        dlg = wx.MessageDialog(self, 'Вы действительно хотите выйти?', 'Подтверждение выхода',
                               wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()

    def ClearForm(self, event):
        if self.is_generated is True and self.is_saved is False:
            dlg = wx.MessageDialog(self,
                                   'Вы уверены, что хотите очистить все поля?\nНесохраненный запрос будет удален навсегда!',
                                   'Подтверждение очистки полей',
                                   wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.textctrl_table_name.Clear()
                self.textctrl_rows_count.Clear()
                self.textctrl_sql.ClearAll()
                self.textctrl_used_tables.Clear()

                self.added_items.clear()
                self.added_item_text.clear()

                for items in self.tree_items.values():
                    for item in items:
                        self.treectrl_databases.SetItemBold(item, False)

                self.is_create_table = False
                self.is_id_column = False

                self.id_column_checkbox.SetValue(False)
                self.id_column_checkbox.Hide()
                self.add_table_checkbox.SetValue(False)
                self.textctrl_increment_start.SetValue('1')
                self.textctrl_increment_start.Hide()
                self.statictext_increment_start.Hide()



    def __init__(self):
        wx.Frame.__init__(self, None, title="SQLDataForge v1.0.1 alpha", size=(800, 600))
        self.SetMinSize((800, 600))
        self.Center()
        self.Maximize()
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        def SetTreeItems():
            self.all_tables = DataController.GetTablesFromDB()
            image_items = wx.ImageList(16, 16)
            database_image = image_items.Add(wx.Image('img/16x16/database.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            table_image = image_items.Add(wx.Image('img/16x16/table.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            self.treectrl_databases.AssignImageList(image_items)

            for key, value in self.all_tables.items():
                temp_items = []
                root = self.treectrl_databases.AddRoot(key)
                self.treectrl_databases.SetItemImage(root, database_image)
                for full_item in value:
                    item = full_item.split(':')[2]
                    child = self.treectrl_databases.AppendItem(root, item)
                    self.treectrl_databases.SetItemImage(child, table_image)
                    temp_items.append(child)
                self.tree_items[root] = temp_items

        def TablePageEnabled(event):
            self.is_create_table = self.add_table_checkbox.GetValue()

            if self.is_create_table:
                self.id_column_checkbox.Show()
            else:
                self.id_column_checkbox.Hide()
                self.statictext_increment_start.Hide()
                self.textctrl_increment_start.Hide()
                self.textctrl_increment_start.SetValue('1')
                self.id_column_checkbox.SetValue(False)
            table_page_panel.Layout()

        def IDColumnEnabled(event):
            self.is_id_column = self.id_column_checkbox.GetValue()

            if self.is_id_column:
                self.statictext_increment_start.Show()
                self.textctrl_increment_start.Show()
            else:
                self.statictext_increment_start.Hide()
                self.textctrl_increment_start.Hide()
                self.textctrl_increment_start.SetValue('1')
            table_page_panel.Layout()

        # -----Обновление списка пБД-----
        result = DataController.SetDatabases()
        if result[0] == 0 and result[1] > 0:
            wx.MessageBox('Добавлено новых пБД: ' + str(result[0]) + ', ошибок: ' + str(result[1]), 'Обновление',
                          wx.OK | wx.ICON_ERROR | wx.CENTRE)
        elif result[0] > 0 and result[1] > 0:
            wx.MessageBox('Добавлено новых пБД: ' + str(result[0]) + ', ошибок: ' + str(result[1]), 'Обновление',
                          wx.OK | wx.ICON_INFORMATION | wx.CENTRE)
        # -------------------------------

        # Главный контейнер
        # --
        main_panel = wx.Panel(self, size=self.GetSize())
        main_boxsizer = wx.BoxSizer(wx.VERTICAL)
        main_panel.SetSizer(main_boxsizer)

        # Меню
        menubar = wx.MenuBar()
        # Файл
        file_menu = wx.Menu()
        generate_menuitem = wx.MenuItem(file_menu, wx.ID_ANY, 'Генерировать \tF9')
        generate_menuitem.SetBitmap(wx.Bitmap('img/16x16/pencil ruler.png'))
        self.Bind(wx.EVT_MENU, self.Generate, generate_menuitem)
        file_menu.Append(generate_menuitem)
        clear_menuitem = wx.MenuItem(file_menu, wx.ID_ANY, 'Очистить \tF3')
        clear_menuitem.SetBitmap(wx.Bitmap('img/16x16/recycle bin sign.png'))
        self.Bind(wx.EVT_MENU, self.ClearForm, clear_menuitem)
        file_menu.Append(clear_menuitem)

        file_menu.AppendSeparator()

        savefile_menuitem = wx.MenuItem(file_menu, wx.ID_ANY, 'Сохранить \tCtrl+S')
        savefile_menuitem.SetBitmap(wx.Bitmap('img/16x16/save.png'))
        self.Bind(wx.EVT_MENU, self.SaveScript, savefile_menuitem)
        file_menu.Append(savefile_menuitem)

        # Формирование меню
        menubar.Append(file_menu, '&Файл')

        # Установка
        self.SetMenuBar(menubar)

        # Панель инструментов
        self.toolbar = self.CreateToolBar()

        self.toolbar.AddTool(1, "Генерировать", wx.Bitmap("img/16x16/pencil ruler.png"),
                             shortHelp="Сгенерировать SQL-код")
        self.Bind(wx.EVT_TOOL, self.Generate, id=1)
        self.toolbar.AddTool(2, "Очистить", wx.Bitmap("img/16x16/recycle bin sign.png"),
                             shortHelp="Очистить поля")
        self.Bind(wx.EVT_TOOL, self.ClearForm, id=2)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(3, "Сохранить", wx.Bitmap("img/16x16/save.png"),
                             shortHelp="Сохранить скрипт")
        self.Bind(wx.EVT_TOOL, self.SaveScript, id=3)

        self.toolbar.Realize()

        # Рабочий контейнер
        # ---
        data_panel = wx.Panel(main_panel)
        data_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        data_panel.SetSizer(data_boxsizer)

        # Дерево баз данных
        self.treectrl_databases = wx.TreeCtrl(data_panel, size=(200, -1))
        data_boxsizer.Add(self.treectrl_databases, 0, wx.LEFT | wx.EXPAND)
        SetTreeItems()
        self.treectrl_databases.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self.treectrl_databases)

        # Контейнер работы с кейсами
        # ----
        table_panel = wx.Panel(data_panel)
        table_boxsizer = wx.BoxSizer(wx.VERTICAL)
        table_panel.SetSizer(table_boxsizer)

        # Notebook настроек
        # -----
        notebook_settings = wx.Notebook(table_panel, size=(-1, 200))

        # Главная
        # ------
        main_page_panel = wx.Panel(notebook_settings)
        main_page_boxsizer = wx.BoxSizer(wx.VERTICAL)
        main_page_panel.SetSizer(main_page_boxsizer)

        # Контейнер "Головной"
        # -------
        header_panel = wx.Panel(main_page_panel, size=(-1, 35))
        header_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        header_panel.SetSizer(header_boxsizer)

        statictext_table_name = wx.StaticText(header_panel, label="Имя таблицы:")
        header_boxsizer.Add(statictext_table_name, 0, wx.LEFT | wx.CENTER | wx.ALL, border=5)

        self.textctrl_table_name = wx.TextCtrl(header_panel, size=(-1, -1))
        header_boxsizer.Add(self.textctrl_table_name, 1, wx.CENTER | wx.EXPAND | wx.ALL, border=5)

        statictext_rows_count = wx.StaticText(header_panel, label="Кол-во строк:")
        header_boxsizer.Add(statictext_rows_count, 0, wx.CENTER | wx.RIGHT | wx.ALL, border=5)

        self.textctrl_rows_count = wx.TextCtrl(header_panel, size=(100, -1))
        header_boxsizer.Add(self.textctrl_rows_count, 0, wx.RIGHT | wx.ALL, border=5)
        # -------
        main_page_boxsizer.Add(header_panel, 0, wx.TOP | wx.EXPAND)
        # -------

        statictext_used_tables = wx.StaticText(main_page_panel, label="Столбцы:")
        main_page_boxsizer.Add(statictext_used_tables, 0, wx.RIGHT | wx.ALL, 5)

        self.textctrl_used_tables = wx.TextCtrl(main_page_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        main_page_boxsizer.Add(self.textctrl_used_tables, 1, wx.RIGHT | wx.LEFT | wx.BOTTOM | wx.EXPAND | wx.ALL, 5)
        # ------
        notebook_settings.AddPage(main_page_panel, "Главная")
        # ------

        # Таблица 
        # ------
        table_page_panel = wx.Panel(notebook_settings)
        table_page_boxsizer = wx.BoxSizer(wx.VERTICAL)
        table_page_panel.SetSizer(table_page_boxsizer)

        self.add_table_checkbox = wx.CheckBox(table_page_panel, label="Создать таблицу")
        table_page_boxsizer.Add(self.add_table_checkbox, 0, wx.ALL, 5)
        self.add_table_checkbox.Bind(wx.EVT_CHECKBOX, TablePageEnabled)

        # -------
        id_column_panel = wx.Panel(table_page_panel)
        id_column_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        id_column_panel.SetSizer(id_column_boxsizer)

        self.id_column_checkbox = wx.CheckBox(id_column_panel, label="Добавить ID для строк таблицы")
        id_column_boxsizer.Add(self.id_column_checkbox, 0, wx.TOP|wx.LEFT|wx.RIGHT, 5)
        self.Bind(wx.EVT_CHECKBOX, IDColumnEnabled)
        self.id_column_checkbox.Hide()

        self.statictext_increment_start = wx.StaticText(id_column_panel, label="Начальное значение ID:")
        id_column_boxsizer.Add(self.statictext_increment_start, 0, wx.TOP|wx.RIGHT|wx.LEFT, 5)
        self.statictext_increment_start.Hide()

        self.textctrl_increment_start = wx.TextCtrl(id_column_panel, size=(100, -1))
        self.textctrl_increment_start.SetValue('1')
        id_column_boxsizer.Add(self.textctrl_increment_start, 0, wx.LEFT, 5)
        self.textctrl_increment_start.Hide()

        table_page_boxsizer.Add(id_column_panel, 0, wx.TOP | wx.EXPAND)
        # -------

        # ------
        notebook_settings.AddPage(table_page_panel, "Таблица")
        # -----
        table_boxsizer.Add(notebook_settings, 0, wx.TOP | wx.EXPAND)
        # -----

        # Редактор кода
        self.textctrl_sql = wx.stc.StyledTextCtrl(table_panel, style=wx.TE_MULTILINE)
        # Настройки шрифта
        self.textctrl_sql.StyleSetFont(wx.stc.STC_STYLE_DEFAULT,
                                       wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.textctrl_sql.StyleClearAll()
        # Подсветка синтаксиса
        sql_keywords = "insert into values create table as text number primary key integer not null"
        self.textctrl_sql.SetLexer(wx.stc.STC_LEX_SQL)
        self.textctrl_sql.SetKeyWords(0, sql_keywords)
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_COMMENT, wx.Colour(196, 69, 105))
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_COMMENTLINE, wx.Colour(196, 69, 105))
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_COMMENTDOC, wx.Colour(196, 69, 105))
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_NUMBER, wx.Colour(30, 36, 96))
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_CHARACTER, wx.Colour(86, 166, 57))
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_STRING, wx.Colour(86, 166, 57))
        self.textctrl_sql.StyleSetForeground(wx.stc.STC_SQL_WORD, wx.Colour(146, 0, 242))
        # Боковое поле
        self.textctrl_sql.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.textctrl_sql.SetMarginWidth(1, 45)
        table_boxsizer.Add(self.textctrl_sql, 1, wx.BOTTOM | wx.LEFT | wx.EXPAND)
        # ----
        data_boxsizer.Add(table_panel, 1, wx.BOTTOM | wx.RIGHT | wx.EXPAND)
        # ----
        # ---
        main_boxsizer.Add(data_panel, 1, wx.BOTTOM | wx.EXPAND)
        # ---

        self.statusbar = self.CreateStatusBar(1, wx.STB_ELLIPSIZE_END)
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusText(self.query_status, 0)
        self.statusbar.SetStatusText("", 1)
        self.statusbar.SetStatusText("asasas", 2)

        main_panel.Layout()
        main_panel.Show()


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
