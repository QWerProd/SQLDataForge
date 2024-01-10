import wx
import wx.stc
import wx.lib.scrolledpanel
import sqlite3
import subprocess
import sys
import webbrowser

from app.tools.recovery import Recovery
from datetime import datetime
from data_controller import DataController
from sql_generator import SQLGenerator
from app.error_catcher import ErrorCatcher
from conn_frames.connection_viewer import ConnectionViewer
from conn_frames.new_conn import NewConnection
from conn_frames.new_udb_wizard import UDBCreateMaster
from single_generator import SimpleGenerator
from app.tools.settings import Settings
from app.tools.logviewer import Logviewer
from app.app_parameters import APP_TEXT_LABELS, APP_PARAMETERS, APP_LOCALES

catcher = ErrorCatcher(APP_PARAMETERS['APP_LANGUAGE'])

# Глобальный лист добавленных столбцов
added_items = []
added_item_text = []
added_item_code = []

# Листы индексов
index_items = []

# Редакторы кода для обновления стилей
stc_redactors = []


class MainFrame(wx.Frame):
    tree_items = {}
    all_tables = {}

    # Переменные "Простого генератора"
    gens = {}
    simplegens_menuitem = []

    # Листы для страницы "Таблица"
    textctrl_column_names = []
    textctrl_column_types = []
    column_items = []

    # Параметры страницы "Таблица"
    is_create_table = False
    is_id_column = False

    # Параметры состояния
    is_generated = False
    is_saved = False
    file_path = ''
    file_name = ''
    query_status = APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.WAITING']

    # Ключевые слова для лексера wx.stc.StyledTextCtrl
    sql_keywords = ("insert into values create table as text number primary key integer not null where and or like"
                    " if exists index on is")

    # Переменная отвечает за изменение индекса обращения к столбцам
    id_added = 0

    # ---------------------------------------------------

    class ColumnItem(wx.Panel):
        rownum = ""
        colname = ""
        coltype = ""
        colcode = ""
        id_colname = ""
        id_coltype = ""

        def __init__(self, parent: wx.Panel, rid: str, column_name="", column_type="", column_code="", is_empty=False):
            super().__init__(parent)
            self.colname = column_name
            self.coltype = column_type
            self.colcode = column_code
            self.id_colname = rid + "0"
            self.id_coltype = rid + "1"

            def on_colname_changed(event):
                # Получаем необходимые значения
                new_colname = textctrl_colname.GetValue()
                item_id = int(textctrl_colname.GetId() / 10)

                # Производим замену имени столбца на новое
                added_item_code[item_id] = new_colname

                # Обновляем значения списков у Индексов
                for item in index_items:
                    item.update_choices(added_item_code)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.SetSizer(sizer)

            if is_empty:
                sizer.AddMany([
                    (wx.TextCtrl(self, style=wx.TE_READONLY, size=(150, -1)), 0, wx.RIGHT, 5),
                    (wx.TextCtrl(self, style=wx.TE_READONLY, size=(150, -1)), 0, wx.RIGHT, 5),
                    (wx.StaticText(self, label=self.colcode, size=(150, -1)), 0, wx.ALIGN_CENTER_VERTICAL, 5)
                ])
                return

            textctrl_colname = wx.TextCtrl(self, int(self.id_colname), size=(150, -1))
            textctrl_colname.SetValue(self.colname)
            textctrl_colname.Bind(wx.EVT_TEXT, on_colname_changed)
            sizer.Add(textctrl_colname, 0, wx.RIGHT, 5)

            textctrl_coltype = wx.TextCtrl(self, int(self.id_coltype), size=(150, -1), style=wx.TE_READONLY)
            textctrl_coltype.SetValue(self.coltype)
            sizer.Add(textctrl_coltype, 0, wx.RIGHT, 5)

            statictext_colcode = wx.StaticText(self, label=self.colcode, size=(150, -1))
            sizer.Add(statictext_colcode, 0, wx.ALIGN_CENTER_VERTICAL, 5)

    # ---------------------------------------------------

    class IndexItem(wx.Panel):

        parent = wx.Panel
        index_name = str
        condition = str
        is_unique = bool

        columns = list

        def update_choices(self, choices: list):
            self.combobox_index_columns.SetItems(choices)

        def index_name_changed(self, event):
            self.index_name = self.textctrl_index_name.GetValue()

        def column_selected(self, event):
            selection = self.combobox_index_columns.GetValue()

            if selection in self.columns:
                self.columns.remove(selection)
            else:
                self.columns.append(selection)

            self.textctrl_columns.SetValue(','.join(self.columns))

        def is_unique_enabled(self, event):
            self.is_unique = self.checkbox_unique.GetValue()

        def condition_changed(self, event):
            self.condition = self.textctrl_condition.GetValue()

            temprows = self.condition.split('\n')
            for row in temprows:
                row.strip()
                if row.startswith('--'):
                    self.condition = self.condition.replace(row, '')

        def get_index(self) -> dict:
            self.index_name = self.index_name.strip()
            if len(self.index_name) == 0:
                catcher.error_message('E008')
            elif len(self.columns) == 0:
                catcher.error_message('E009')
            else:
                index = dict()
                index['index_name'] = self.index_name
                index['columns'] = self.columns
                index['is_unique'] = self.is_unique
                index['condition'] = self.condition
                return index

        def selfdestroy(self, event):
            index_items.remove(self)
            self.Destroy()
            self.parent.Layout()

        def __init__(self, parent, index_num: int):
            super().__init__(parent)
            self.parent = parent
            self.index_name = 'new_index' + str(index_num)
            self.columns = []
            self.condition = ''
            self.is_unique = False

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            # ---------------------------------
            first_panel = wx.Panel(self)
            first_sizer = wx.BoxSizer(wx.HORIZONTAL)
            first_panel.SetSizer(first_sizer)

            self.textctrl_index_name = wx.TextCtrl(first_panel, size=(125, -1))
            self.textctrl_index_name.SetValue(self.index_name)
            self.textctrl_index_name.Bind(wx.EVT_TEXT, self.index_name_changed)
            first_sizer.AddMany([(wx.StaticText(first_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.INDEX_PAGE.INDEX_NAME'], size=(75, -1)),
                                  0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                                 (self.textctrl_index_name, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])

            self.combobox_index_columns = wx.ComboBox(first_panel, choices=added_item_code, size=(225, -1))
            self.combobox_index_columns.Bind(wx.EVT_COMBOBOX, self.column_selected)
            first_sizer.AddMany([(wx.StaticText(first_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.INDEX_PAGE.INDEX_COLUMNS'], size=(55, -1)),
                                  0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                                 (self.combobox_index_columns, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)])
            # ---------------------------------
            self.sizer.Add(first_panel, 0, wx.ALL, 0)

            # ---------------------------------
            second_panel = wx.Panel(self)
            second_sizer = wx.BoxSizer(wx.HORIZONTAL)
            second_panel.SetSizer(second_sizer)

            self.checkbox_unique = wx.CheckBox(second_panel, label="UNIQUE", size=(75, -1))
            self.checkbox_unique.Bind(wx.EVT_CHECKBOX, self.is_unique_enabled)
            self.checkbox_unique.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.checkbox_unique.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            second_sizer.Add(self.checkbox_unique, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

            self.button_delete = wx.Button(second_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.INDEX_PAGE.DELETE_INDEX'],
                                           style=wx.NO_BORDER, size=(81, -1))
            self.button_delete.SetBitmapLabel(wx.Bitmap('img/16x16/minus.png', wx.BITMAP_TYPE_PNG))
            self.button_delete.SetBackgroundColour(wx.Colour(255, 225, 225))
            self.button_delete.Bind(wx.EVT_ENTER_WINDOW,
                                    lambda x: self.button_delete.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            self.button_delete.Bind(wx.EVT_BUTTON, self.selfdestroy)
            second_sizer.Add(self.button_delete, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

            self.textctrl_columns = wx.TextCtrl(second_panel, size=(225, -1), style=wx.TE_READONLY)
            self.textctrl_columns.Bind(wx.EVT_ENTER_WINDOW,
                                       lambda x: self.textctrl_columns.SetCursor(wx.NullCursor))
            second_sizer.Add(self.textctrl_columns, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 109)

            # ---------------------------------
            self.sizer.Add(second_panel, 0, wx.BOTTOM, 5)

            # ---------------------------------
            self.textctrl_condition = wx.stc.StyledTextCtrl(self, style=wx.TE_MULTILINE, size=(505, 75))
            stc_redactors.append(self.textctrl_condition)
            self.textctrl_condition.SetValue(APP_TEXT_LABELS['MAIN.MAIN_PANEL.INDEX_PAGE.ENTER_CONDITION_HERE'] + '\n')
            MainFrame.stc_reset_style(self.textctrl_condition)
            self.textctrl_condition.Bind(wx.stc.EVT_STC_CHANGE, self.condition_changed)

            self.sizer.Add(self.textctrl_condition, 0, wx.ALL, 0)

            self.Layout()

    # ---------------------------------------------------

    def on_activated(self, evt):
        # Получение выбранного элемента и проверка, является ли он НЕ базой данных
        get_item = evt.GetItem()
        activated = self.treectrl_databases.GetItemText(get_item)
        if activated.endswith('.db'):
            return
        else:
            add_act = ""
            get_parent = self.treectrl_databases.GetItemParent(get_item)
            parent_name = self.treectrl_databases.GetItemText(get_parent)

            # Поиск таблицы
            for key in self.all_tables:
                if key != parent_name:
                    continue
                else:
                    for item in self.all_tables[key]:
                        if item.find(activated) != -1:
                            add_act = key + ":" + item
                            break

            # Переопределение массивов элементов и выделения выбранных элементов в дереве
            if len(added_items) <= 0:
                added_items.append(add_act)
                added_item_text.append(activated)
                added_item_code.append(add_act.split(':')[2])
                self.treectrl_databases.SetItemBold(get_item, True)
                self.textctrl_column_names.append(add_act.split(':')[2])
                self.textctrl_column_types.append(add_act.split(':')[3])
            else:
                is_removed = False
                for item in added_items:
                    if activated in item:
                        added_items.remove(add_act)
                        added_item_text.remove(activated)
                        added_item_code.remove(add_act.split(':')[2])
                        self.treectrl_databases.SetItemBold(get_item, False)
                        self.textctrl_column_names.remove(add_act.split(':')[2])
                        self.textctrl_column_types.remove(add_act.split(':')[3])
                        is_removed = True
                        break
                if not is_removed:
                    added_items.append(add_act)
                    added_item_text.append(activated)
                    added_item_code.append(add_act.split(':')[2])
                    self.treectrl_databases.SetItemBold(get_item, True)
                    self.textctrl_column_names.append(add_act.split(':')[2])
                    self.textctrl_column_types.append(add_act.split(':')[3])
            self.table_columns_regulate()

    def table_columns_regulate(self):
        self.table_items_panel.DestroyChildren()
        self.table_items_sizer.Clear(True)
        self.column_items.clear()
        items = []

        if self.is_id_column:
            self.column_items.append([self.ColumnItem(self.table_items_panel, '0', 'id', 'INTEGER'),
                                      '00', '01'])
            items.append((self.column_items[0][0], 0, wx.ALL, 0))
            self.id_added = 1

        for i in range(0, len(self.textctrl_column_names)):
            self.column_items.append([self.ColumnItem(self.table_items_panel, str(i + self.id_added), self.textctrl_column_names[i],
                                                      self.textctrl_column_types[i], added_item_text[i]),
                                      str(i + self.id_added) + "0", str(i + self.id_added) + "1"])
            items.append((self.column_items[i + self.id_added][0], 0, wx.ALL, 0))
        self.column_items.append(self.ColumnItem(self.table_items_panel, "-1", is_empty=True))
        items.append((self.column_items[len(self.column_items) - 1], 0, wx.ALL, 0))

        # Обновляем значения списков у Индексов
        for item in index_items:
            item.update_choices(added_item_code)

        self.table_items_sizer.AddMany(items)
        self.table_items_panel.Layout()
        self.table_columns_panel.Layout()

    def generate(self, event):
        self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        start_generate_time = datetime.now()

        table_info = {}
        indexes_info = []
        table_name = self.textctrl_table_name.GetValue()
        rows_count = self.textctrl_rows_count.GetValue()

        self.query_status = APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.GENERATING']
        self.statusbar.SetStatusText(self.query_status, 0)

        if len(added_items) == 0:
            self.query_status = catcher.error_message('E003')
            self.SetCursor(wx.NullCursor)
            self.statusbar.SetStatusText(self.query_status, 0)
        elif table_name == '':
            self.query_status = catcher.error_message('E004')
            self.SetCursor(wx.NullCursor)
            self.statusbar.SetStatusText(self.query_status, 0)
        elif rows_count == '':
            self.query_status = catcher.error_message('E005')
            self.SetCursor(wx.NullCursor)
            self.statusbar.SetStatusText(self.query_status, 0)
        else:
            try:
                rows_count = int(rows_count)
                if rows_count <= 0:
                    self.query_status = catcher.error_message('E006')
                    self.statusbar.SetStatusText(self.query_status, 0)
                    return

                # Составление словаря со значениями для создания скрипта таблицы
                temp = {'is_id_create': False}
                if self.is_create_table:
                    id_create = self.id_column_checkbox.GetValue()
                    temp['is_id_create'] = id_create
                    if self.is_id_column:
                        increment = self.textctrl_increment_start.GetValue()
                        temp['increment_start'] = increment
                table_info[table_name] = temp

                # Составление словарей со значениями для создания скриптов индексов
                for item in index_items:
                    if item is None:
                        return
                    else:
                        indexes_info.append(item.get_index())

                # Проверка имен индексов на уникальность
                temp_indexes = []
                for col in indexes_info:
                    temp_indexes.append(col['index_name'])
                visited = set()
                dup = [x for x in temp_indexes if x in visited or (visited.add(x) or False)]
                if len(dup) > 0:
                    self.query_status = catcher.error_message('E011')
                    self.statusbar.SetStatusText(self.query_status, 0)
                    return

                # Получение значений имен столбцов
                colnames = []
                for i in range(len(added_items)):
                    old_coltype = added_items[i].split(':')[3]

                    new_colname = added_item_code[i + self.id_added]
                    textctrl_coltype = self.table_items_panel.FindWindowById(int(self.column_items[i + self.id_added][2]))
                    new_coltype = textctrl_coltype.GetValue()

                    colnames.append(new_colname)
                    added_items[i] = added_items[i].replace(old_coltype, new_coltype)

                # Проверка имен столбцов на уникальность
                temp_cols = []
                for col in colnames:
                    temp_cols.append(col)
                visited = set()
                dup = [x for x in temp_cols if x in visited or (visited.add(x) or False)]
                if len(dup) > 0:
                    self.query_status = catcher.error_message('E007')
                    self.statusbar.SetStatusText(self.query_status, 0)
                else:
                    # Генерация
                    with sqlite3.connect('app/app.db') as app_conn:
                        cursor = app_conn.cursor()
                        start_build_time = datetime.now()
                        builder = SQLGenerator(app_conn, rows_count, added_items, colnames, table_info, indexes_info)
                        query = ''
                        query += builder.BuildQuery(self.is_create_table)
                        build_time = datetime.now() - start_build_time
                        self.textctrl_sql.SetValue(query)
                        self.is_generated = True
                        self.is_saved = False
                        self.query_status = APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.DONE']
                        self.statusbar.SetStatusText(self.query_status, 0)
                        generate_time = datetime.now() - start_generate_time

                        # Запись запроса в лог
                        cursor = app_conn.cursor()
                        cursor.execute(f"""INSERT INTO t_execution_log(query_text, date_execute)
                                           VALUES (?, ?);""", (query, datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')))
                        app_conn.commit()

                    # Подсчет времени работы
                    build_time = round(build_time.total_seconds(), 4)
                    generate_time = round(generate_time.total_seconds(), 2)
                    self.statusbar.SetStatusText(APP_TEXT_LABELS['MAIN.STATUSBAR.TIMER.GENERATE_TIME'] + str(build_time)
                                                 + APP_TEXT_LABELS['MAIN.STATUSBAR.TIMER.ALL_TIME'] + str(generate_time) + " с.", 2)
            except ValueError:
                self.query_status = catcher.error_message('E010')
                self.statusbar.SetStatusText(self.query_status, 0)
            finally:
                self.SetCursor(wx.NullCursor)
                cursor.close()

    def save_script(self, file_path: str = None):
        sql = self.textctrl_sql.GetValue()
        if sql == "":
            self.query_status = catcher.error_message('E001')
            self.statusbar.SetStatusText(self.query_status, 0)
        else:
            if file_path is None or file_path == '':
                with wx.FileDialog(self, APP_TEXT_LABELS['FILE_DIALOG.CAPTION_SAVE'],
                                   wildcard=APP_TEXT_LABELS['FILE_DIALOG.WILDCARD_SQL'],
                                   style=wx.FD_SAVE) as file_dialog:
                    if file_dialog.ShowModal() == wx.ID_CANCEL:
                        return

                    file_path = file_dialog.GetPath()
                    file_name = file_dialog.GetFilename()

                    if not file_path.endswith('.sql'):
                        file_name += '.sql'
                        file_path += '.sql'
                    self.file_name = file_name
                    self.file_path = file_path

            with open(self.file_path, mode='w', encoding="utf-8") as reader:
                reader.write(sql)
            wx.MessageBox(APP_TEXT_LABELS['MAIN.MESSAGE_BOX.SAVE_SCRIPT.FILE'] + self.file_name +
                          APP_TEXT_LABELS['MAIN.MESSAGE_BOX.SAVE_SCRIPT.SAVED'] + self.file_path,
                          APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.SAVED'], wx.ICON_INFORMATION | wx.OK, self)
            self.is_saved = True
            self.query_status = APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.SAVED'] + ' - ' + self.file_name
            self.statusbar.SetStatusText(self.query_status, 0)
            self.SetTitle('SDForge - ' + self.file_name)

    def save(self, event):
        self.save_script(self.file_path)

    def save_as(self, event):
        self.save_script()

    def clear_form(self, event):
        if self.is_generated is True and self.is_saved is False:
            dlg = wx.MessageDialog(self,
                                   APP_TEXT_LABELS['MAIN.MESSAGE_BOX.CLEAR_FORM.MESSAGE'],
                                   APP_TEXT_LABELS['MAIN.MESSAGE_BOX.CLEAR_FORM.CAPTION'],
                                   wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.textctrl_table_name.Clear()
                self.textctrl_rows_count.Clear()
                self.textctrl_sql.ClearAll()

                added_items.clear()
                added_item_text.clear()
                self.textctrl_column_names.clear()
                self.textctrl_column_types.clear()

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

                self.table_columns_regulate()

                self.query_status = APP_TEXT_LABELS['MAIN.STATUSBAR.STATUS.WAITING']
                self.statusbar.SetStatusText(self.query_status, 0)
                self.statusbar.SetStatusText("", 2)

    def refresh(self, event):
        self.treectrl_databases.DeleteChildren(self.treectrl_databases_root)
        self.all_tables = DataController.GetTablesFromDB()
        self.set_tree_items()

    def set_tree_items(self):
        for key, value in self.all_tables.items():
            temp_items = []
            root = self.treectrl_databases.AppendItem(self.treectrl_databases_root, key)
            if len(value) > 0:
                self.treectrl_databases.SetItemImage(root, self.database_image)
                for full_item in value:
                    item = full_item.split(':')[3]
                    child = self.treectrl_databases.AppendItem(root, item)
                    self.treectrl_databases.SetItemImage(child, self.table_image)
                    temp_items.append(child)
                self.tree_items[root] = temp_items
            else:
                pass
                # self.treectrl_databases.SetItemImage(root, )

    def delete_index(self, item):
        index_items.remove(item)
        item.Hide()
        self.indexes_scrolledwindow.Layout()

    # Открывашки для других окон
    ############################
    def open_new_connection(self, event):
        new_conn = NewConnection()
        new_conn.Show()
        new_conn.SetFocus()

    def open_connection_viewer(self, event):
        conn_viewer = ConnectionViewer()
        conn_viewer.Show()
        conn_viewer.SetFocus()

    def open_newudb_master(self, event):
        create_master = UDBCreateMaster(catcher)
        create_master.Show()
        create_master.SetFocus()

    def open_settings_frame(self, event):
        with Settings(self) as sett:
            res = sett.ShowModal()
            if res > 0:
                self.update_stc_style()
            if res > 1:
                self.relaunch_app()
                self.Destroy()

    def open_simple_generator_from_menu(self, event):
        menuitem = self.menubar.FindItemById(event.GetId())

        for simpgen_menuitem in self.simpgens_menuitems:
            if menuitem in simpgen_menuitem:
                item_code = simpgen_menuitem[1]
                simple_generator = SimpleGenerator(catcher, item_code)
                simple_generator.Show()
                simple_generator.SetFocus()
                break

    def open_recovery(self, event):
        recovery = Recovery(catcher)
        recovery.Show()
        recovery.SetFocus()

    def open_logviewer(self, event):
        logviewer = Logviewer(catcher)
        logviewer.Show()
        logviewer.SetFocus()

    def open_app_info(self, event):
        about_app = AboutApp()
        about_app.Show()
        about_app.SetFocus()

    ############################

    def close_app(self, event):
        if APP_PARAMETERS['IS_CATCH_CLOSING_APP'] == 'True':
            result = wx.MessageBox(APP_TEXT_LABELS['MAIN.MESSAGE_BOX.CLOSE_APP.MESSAGE'],
                                   APP_TEXT_LABELS['MAIN.MESSAGE_BOX.CLOSE_APP.MESSAGE'],
                                   wx.YES_NO | wx.NO_DEFAULT, self)
            if result == wx.YES:
                self.Destroy()
                exit()
            else:
                return
        else:
            self.Destroy()
            exit()

    @staticmethod
    def relaunch_app():
        new_process = subprocess.Popen([sys.executable] + sys.argv)

    # Статические методы для обновления при изменениях в приложении
    ###############################################################

    def update_stc_style(self):
        for redactor in stc_redactors:
            self.stc_reset_style(redactor)

    @staticmethod
    def stc_reset_style(stc_redactor: wx.stc.StyledTextCtrl):
        # Настройки шрифта
        stc_redactor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT,
                                  wx.Font(pointSize=int(APP_PARAMETERS['STC_FONT_SIZE']),
                                          family=wx.FONTFAMILY_TELETYPE,
                                          style=wx.FONTSTYLE_NORMAL,
                                          weight=int(APP_PARAMETERS['STC_FONT_BOLD'])))
        stc_redactor.StyleClearAll()
        # Подсветка синтаксиса
        stc_redactor.SetLexer(wx.stc.STC_LEX_SQL)
        stc_redactor.SetKeyWords(0, MainFrame.sql_keywords)
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENT, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENTLINE, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENTDOC, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_NUMBER, APP_PARAMETERS['STC_COLOUR_NUMBER'])
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_CHARACTER, APP_PARAMETERS['STC_COLOUR_STRING'])
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_STRING, APP_PARAMETERS['STC_COLOUR_STRING'])
        stc_redactor.StyleSetForeground(wx.stc.STC_SQL_WORD, APP_PARAMETERS['STC_COLOUR_WORD'])
        # Боковое поле
        stc_redactor.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        stc_redactor.SetMarginWidth(1, 45)

        ###############################################################

    def __init__(self):
        wx.Frame.__init__(self, None, title="SDForge", size=(800, 600))
        self.SetMinSize((800, 600))
        self.Maximize()
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))
        self.Bind(wx.EVT_CLOSE, self.close_app)

        # Локаль приложения
        locale = wx.Locale(APP_LOCALES[APP_PARAMETERS['APP_LANGUAGE']], wx.LOCALE_LOAD_DEFAULT)

        def is_table_enabled(event):
            self.is_create_table = self.add_table_checkbox.GetValue()
            self.is_id_column = False

            if self.is_create_table:
                self.id_column_checkbox.Show()
            else:
                self.id_column_checkbox.Hide()
                self.statictext_increment_start.Hide()
                self.textctrl_increment_start.Hide()
                self.textctrl_increment_start.SetValue('1')
                self.id_column_checkbox.SetValue(False)
            self.table_columns_regulate()
            table_page_panel.Layout()

        def is_id_enabled(event):
            self.is_id_column = self.id_column_checkbox.GetValue()

            if self.is_id_column:
                added_item_code.insert(0, 'id')
                self.statictext_increment_start.Show()
                self.textctrl_increment_start.Show()
            else:
                added_item_code.remove('id')
                self.statictext_increment_start.Hide()
                self.textctrl_increment_start.Hide()
                self.textctrl_increment_start.SetValue('1')
            self.table_columns_regulate()
            table_page_panel.Layout()

        def create_index(event):
            index_item = self.IndexItem(self.indexes_scrolledwindow, len(index_items) + 1)
            index_items.append(index_item)
            self.indexes_sizer.Add(index_item, 0, wx.BOTTOM, 5)
            self.indexes_sizer.Layout()
            self.indexes_scrolledwindow.SetupScrolling()

        # -----Обновление списка пБД-----
        result = DataController.SetDatabases()
        if result[0] == 0 and result[1] > 0:
            wx.MessageBox(APP_TEXT_LABELS['MAIN.MESSAGE_BOX.INIT.MESSAGE1'] + str(result[0]) +
                          APP_TEXT_LABELS['MAIN.MESSAGE_BOX.INIT.MESSAGE2'] + str(result[1]),
                          APP_TEXT_LABELS['MAIN.MESSAGE_BOX.INIT.CAPTION'],
                          wx.OK | wx.ICON_ERROR | wx.CENTRE)
        elif result[0] > 0 and result[1] > 0:
            wx.MessageBox(APP_TEXT_LABELS['MAIN.MESSAGE_BOX.INIT.MESSAGE1'] + str(result[0]) +
                          APP_TEXT_LABELS['MAIN.MESSAGE_BOX.INIT.MESSAGE2'] + str(result[1]),
                          APP_TEXT_LABELS['MAIN.MESSAGE_BOX.INIT.CAPTION'],
                          wx.OK | wx.ICON_INFORMATION | wx.CENTRE)
        # -------------------------------

        # Главный контейнер
        # --
        main_panel = wx.Panel(self, size=self.GetSize())
        main_boxsizer = wx.BoxSizer(wx.VERTICAL)
        main_panel.SetSizer(main_boxsizer)

        # Меню
        self.menubar = wx.MenuBar()

        # Файл
        # ----------
        self.file_menu = wx.Menu()
        generate_menuitem = wx.MenuItem(self.file_menu, wx.ID_ANY,
                                        APP_TEXT_LABELS['MAIN.MAIN_MENU.FILE.GENERATE'] + ' \t' + APP_PARAMETERS['KEY_EXECUTE'])
        generate_menuitem.SetBitmap(wx.Bitmap('img/16x16/pencil ruler.png'))
        self.Bind(wx.EVT_MENU, self.generate, generate_menuitem)
        self.file_menu.Append(generate_menuitem)

        refresh_menuitem = wx.MenuItem(self.file_menu, wx.ID_ANY,
                                       APP_TEXT_LABELS['MAIN.MAIN_MENU.FILE.REFRESH'] + '\t' + APP_PARAMETERS['KEY_REFRESH'])
        refresh_menuitem.SetBitmap(wx.Bitmap('img/16x16/update.png'))
        self.Bind(wx.EVT_MENU, self.refresh, refresh_menuitem)
        self.file_menu.Append(refresh_menuitem)

        clear_menuitem = wx.MenuItem(self.file_menu, wx.ID_ANY,
                                     APP_TEXT_LABELS['MAIN.MAIN_MENU.FILE.CLEAR_ALL'] + '\t' + APP_PARAMETERS['KEY_CLEAR_ALL'])
        clear_menuitem.SetBitmap(wx.Bitmap('img/16x16/recycle bin sign.png'))
        self.Bind(wx.EVT_MENU, self.clear_form, clear_menuitem)
        self.file_menu.Append(clear_menuitem)

        self.file_menu.AppendSeparator()

        savefile_menuitem = wx.MenuItem(self.file_menu, wx.ID_ANY,
                                        APP_TEXT_LABELS['BUTTON.SAVE'] + '\t' + APP_PARAMETERS['KEY_SAVE_SQL'])
        savefile_menuitem.SetBitmap(wx.Bitmap('img/16x16/save.png'))
        self.Bind(wx.EVT_MENU, self.save, savefile_menuitem)
        self.file_menu.Append(savefile_menuitem)
        savefile_as_menuitem = wx.MenuItem(self.file_menu, wx.ID_ANY,
                                           APP_TEXT_LABELS['BUTTON.SAVE_AS'] + '\t' + APP_PARAMETERS['KEY_SAVE_AS'])
        savefile_as_menuitem.SetBitmap(wx.Bitmap('img/16x16/save as.png'))
        self.Bind(wx.EVT_MENU, self.save_as, savefile_as_menuitem)
        self.file_menu.Append(savefile_as_menuitem)

        # Подключения
        # ----------
        self.connect_menu = wx.Menu()
        add_connect_menuitem = wx.MenuItem(self.connect_menu, wx.ID_ANY,
                                           APP_TEXT_LABELS['MAIN.MAIN_MENU.CONNECTIONS.ADD_UDB'] + '\t' + APP_PARAMETERS['KEY_NEW_INSTANCE'])
        add_connect_menuitem.SetBitmap(wx.Bitmap('img/16x16/database  add.png'))
        self.Bind(wx.EVT_MENU, self.open_new_connection, add_connect_menuitem)
        self.connect_menu.Append(add_connect_menuitem)

        create_udb_menuitem = wx.MenuItem(self.connect_menu, wx.ID_ANY,
                                          APP_TEXT_LABELS['MAIN.MAIN_MENU.CONNECTIONS.CREATE_UDB'] + '\t' + APP_PARAMETERS['KEY_CREATE_UDB_WIZARD'])
        create_udb_menuitem.SetBitmap(wx.Bitmap('img/16x16/case.png'))
        self.Bind(wx.EVT_MENU, self.open_newudb_master, create_udb_menuitem)
        self.connect_menu.Append(create_udb_menuitem)

        self.connect_menu.AppendSeparator()

        view_connects_menuitem = wx.MenuItem(self.connect_menu, wx.ID_ANY,
                                             APP_TEXT_LABELS['MAIN.MAIN_MENU.CONNECTIONS.UDB_VIEWER'] + '\t' + APP_PARAMETERS['KEY_UDB_VIEWER'])
        view_connects_menuitem.SetBitmap(wx.Bitmap('img/16x16/marked list points.png'))
        self.Bind(wx.EVT_MENU, self.open_connection_viewer, view_connects_menuitem)
        self.connect_menu.Append(view_connects_menuitem)

        # Генератор
        # ----------
        generator_menu = wx.Menu()
        self.gens = DataController.BuildDictOfGens()
        self.simpgens_menuitems = []
        for database, gen in self.gens.items():
            database_menuitem = wx.Menu()
            if database == 'simple':
                generator_menu.AppendSubMenu(database_menuitem, '&' + APP_TEXT_LABELS['MAIN.MAIN_MENU.GENERATOR.SIMPLE_GENERATORS'])
                generator_menu.AppendSeparator()
            else:
                generator_menu.AppendSubMenu(database_menuitem, f'&{database}')

            for item in gen:
                gen_menuitem = wx.MenuItem(database_menuitem, wx.ID_ANY, item[1])
                self.Bind(wx.EVT_MENU, self.open_simple_generator_from_menu, gen_menuitem)
                database_menuitem.Append(gen_menuitem)
                self.simpgens_menuitems.append([gen_menuitem, item[0]])

        # Инструменты
        # ----------
        self.tools_menu = wx.Menu()
        recovery_menuitem = wx.MenuItem(self.tools_menu, wx.ID_ANY,
                                        APP_TEXT_LABELS['MAIN.MAIN_MENU.TOOLS.RECOVERY'] + '\t' + APP_PARAMETERS['KEY_RECOVERY'])
        recovery_menuitem.SetBitmap(wx.Bitmap('img/16x16/database.png'))
        self.Bind(wx.EVT_MENU, self.open_recovery, recovery_menuitem)
        self.tools_menu.Append(recovery_menuitem)
        logviewer_menuitem = wx.MenuItem(self.tools_menu, wx.ID_ANY,
                                         APP_TEXT_LABELS['MAIN.MAIN_MENU.TOOLS.LOGVIEWER'] + '\t' + APP_PARAMETERS['KEY_LOGVIEWER'])
        logviewer_menuitem.SetBitmap(wx.Bitmap('img/16x16/history.png'))
        self.Bind(wx.EVT_MENU, self.open_logviewer, logviewer_menuitem)
        self.tools_menu.Append(logviewer_menuitem)
        self.tools_menu.AppendSeparator()
        settings_menuitem = wx.MenuItem(self.tools_menu, wx.ID_ANY,
                                        APP_TEXT_LABELS['MAIN.MAIN_MENU.TOOLS.SETTINGS'] + '\t' + APP_PARAMETERS['KEY_SETTINGS'])
        settings_menuitem.SetBitmap(wx.Bitmap('img/16x16/options.png'))
        self.Bind(wx.EVT_MENU, self.open_settings_frame, settings_menuitem)
        self.tools_menu.Append(settings_menuitem)

        # Справка
        # ----------
        self.info_menu = wx.Menu()
        about_app = wx.MenuItem(self.info_menu, wx.ID_ANY,
                                APP_TEXT_LABELS['MAIN.MAIN_MENU.INFO.ABOUT_APP'])
        about_app.SetBitmap(wx.Bitmap('img/16x16/home.png'))
        self.Bind(wx.EVT_MENU, self.open_app_info, about_app)
        self.info_menu.Append(about_app)

        # Формирование меню
        self.menubar.Append(self.file_menu, '&' + APP_TEXT_LABELS['MAIN.MAIN_MENU.FILE'])
        self.menubar.Append(self.connect_menu, '&' + APP_TEXT_LABELS['MAIN.MAIN_MENU.CONNECTIONS'])
        self.menubar.Append(generator_menu, '&' + APP_TEXT_LABELS['MAIN.MAIN_MENU.GENERATOR'])
        self.menubar.Append(self.tools_menu, '&' + APP_TEXT_LABELS['MAIN.MAIN_MENU.TOOLS'])
        self.menubar.Append(self.info_menu, '&' + APP_TEXT_LABELS['MAIN.MAIN_MENU.INFO'])

        # Установка
        self.SetMenuBar(self.menubar)

        # Панель инструментов
        self.toolbar = self.CreateToolBar()

        self.toolbar.AddTool(1, "Генерировать", wx.Bitmap("img/16x16/pencil ruler.png"),
                             shortHelp=APP_TEXT_LABELS['MAIN.TOOLBAR.SHORTHELP.GENERATE'])
        self.Bind(wx.EVT_TOOL, self.generate, id=1)
        self.toolbar.AddTool(2, "Очистить", wx.Bitmap("img/16x16/recycle bin sign.png"),
                             shortHelp=APP_TEXT_LABELS['MAIN.TOOLBAR.SHORTHELP.CLEAR_ALL'])
        self.Bind(wx.EVT_TOOL, self.clear_form, id=2)
        self.toolbar.AddTool(3, "Обновить", wx.Bitmap("img/16x16/update.png"),
                             shortHelp=APP_TEXT_LABELS['MAIN.TOOLBAR.SHORTHELP.REFRESH'])
        self.Bind(wx.EVT_TOOL, self.refresh, id=3)
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(4, "Сохранить", wx.Bitmap("img/16x16/save.png"),
                             shortHelp=APP_TEXT_LABELS['MAIN.TOOLBAR.SHORTHELP.SAVE_SQL'])
        self.Bind(wx.EVT_TOOL, self.save, id=4)
        self.toolbar.AddTool(5, "Сохранить как", wx.Bitmap("img/16x16/save as.png"),
                             shortHelp=APP_TEXT_LABELS['BUTTON.SAVE_AS'])
        self.Bind(wx.EVT_TOOL, self.save_as, id=5)

        self.toolbar.Realize()

        # Рабочий контейнер
        # ----------
        data_panel = wx.SplitterWindow(main_panel, style=wx.SP_LIVE_UPDATE)

        # Дерево баз данных
        self.treectrl_databases = wx.TreeCtrl(data_panel, size=(200, -1), style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT)
        self.treectrl_databases_root = self.treectrl_databases.AddRoot('')
        self.all_tables = DataController.GetTablesFromDB()
        self.image_items = wx.ImageList(16, 16)
        self.database_image = self.image_items.Add(wx.Image('img/16x16/database.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.invalid_db_image = self.image_items.Add(wx.Image('img/16x16/delete database.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.table_image = self.image_items.Add(wx.Image('img/16x16/table.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.treectrl_databases.AssignImageList(self.image_items)
        self.set_tree_items()
        self.treectrl_databases.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_activated, self.treectrl_databases)

        # Контейнер работы с кейсами
        # ----------
        table_panel = wx.SplitterWindow(data_panel, style=wx.SP_LIVE_UPDATE, size=(1000, -1))

        # Notebook настроек
        # --------------------
        notebook_settings = wx.Notebook(table_panel, size=(-1, 350))

        # Главная
        # ------------------------------
        main_page_panel = wx.Panel(notebook_settings)
        main_page_boxsizer = wx.BoxSizer(wx.VERTICAL)
        main_page_panel.SetSizer(main_page_boxsizer)

        # Контейнер "Головной"
        # ----------------------------------------
        header_panel = wx.Panel(main_page_panel, size=(-1, 35))
        header_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        header_panel.SetSizer(header_boxsizer)

        statictext_table_name = wx.StaticText(header_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE.TABLE_NAME'])
        header_boxsizer.Add(statictext_table_name, 0, wx.LEFT | wx.CENTER | wx.ALL, 5)

        self.textctrl_table_name = wx.TextCtrl(header_panel, size=(-1, -1))
        header_boxsizer.Add(self.textctrl_table_name, 1, wx.CENTER | wx.EXPAND | wx.ALL, 5)

        statictext_rows_count = wx.StaticText(header_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE.ROW_COUNT'])
        header_boxsizer.Add(statictext_rows_count, 0, wx.CENTER | wx.RIGHT | wx.ALL, 5)

        self.textctrl_rows_count = wx.TextCtrl(header_panel, size=(100, -1))
        header_boxsizer.Add(self.textctrl_rows_count, 0, wx.RIGHT | wx.ALL, 5)
        # ----------------------------------------
        main_page_boxsizer.Add(header_panel, 0, wx.EXPAND, 5)
        main_page_boxsizer.Add(wx.StaticLine(main_page_panel), 0, wx.EXPAND | wx.BOTTOM, 5)
        # ----------------------------------------

        # ----------------------------------------
        self.table_columns_panel = wx.Panel(main_page_panel, size=(-1, -1))
        self.table_columns_sizer = wx.BoxSizer(wx.VERTICAL)
        self.table_columns_panel.SetSizer(self.table_columns_sizer)

        # ----------------------------------------
        table_columns_statictext_panel = wx.Panel(self.table_columns_panel)
        tcs_sizer = wx.BoxSizer(wx.HORIZONTAL)
        table_columns_statictext_panel.SetSizer(tcs_sizer)

        statictext_column_name = wx.StaticText(table_columns_statictext_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_NAME'], size=(150, -1))
        tcs_sizer.Add(statictext_column_name, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        statictext_column_type = wx.StaticText(table_columns_statictext_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_TYPE'], size=(150, -1))
        tcs_sizer.Add(statictext_column_type, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        tcs_sizer.Add(wx.StaticText(table_columns_statictext_panel, label='', size=(200, -1)), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        # ----------------------------------------
        self.table_columns_sizer.Add(table_columns_statictext_panel, 0, wx.ALL)
        # ----------------------------------------

        self.table_items_panel = wx.Panel(self.table_columns_panel)
        self.table_items_sizer = wx.BoxSizer(wx.VERTICAL)
        self.table_items_panel.SetSizer(self.table_items_sizer)

        self.empty_item = self.ColumnItem(self.table_items_panel, "0",  is_empty=True)
        self.table_items_sizer.Add(self.empty_item, 0, wx.ALL, 5)
        # ----------------------------------------
        self.table_columns_sizer.Add(self.table_items_panel, 1, wx.ALL)

        # ----------------------------------------
        main_page_boxsizer.Add(self.table_columns_panel, 1, wx.ALL)
        # ----------------------------------------

        # ------------------------------
        notebook_settings.AddPage(main_page_panel, APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE'])
        # ------------------------------

        # Таблица 
        # ------------------------------
        table_page_panel = wx.Panel(notebook_settings)
        table_page_boxsizer = wx.BoxSizer(wx.VERTICAL)
        table_page_panel.SetSizer(table_page_boxsizer)

        self.add_table_checkbox = wx.CheckBox(table_page_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.TABLE_PAGE.CREATE_TABLE'])
        table_page_boxsizer.Add(self.add_table_checkbox, 0, wx.ALL, 5)
        self.add_table_checkbox.Bind(wx.EVT_CHECKBOX, is_table_enabled)
        self.add_table_checkbox.Bind(wx.EVT_ENTER_WINDOW,
                                     lambda x: self.add_table_checkbox.SetCursor(wx.Cursor(wx.CURSOR_HAND)))

        table_page_boxsizer.Add(wx.StaticLine(table_page_panel), 0, wx.EXPAND | wx.ALL, 0)

        # ----------------------------------------
        id_column_panel = wx.Panel(table_page_panel)
        id_column_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
        id_column_panel.SetSizer(id_column_boxsizer)

        self.id_column_checkbox = wx.CheckBox(id_column_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.TABLE_PAGE.ADD_ID'])
        id_column_boxsizer.Add(self.id_column_checkbox, 0, wx.TOP | wx.LEFT | wx.RIGHT, 5)
        self.id_column_checkbox.Bind(wx.EVT_CHECKBOX, is_id_enabled)
        self.id_column_checkbox.Bind(wx.EVT_ENTER_WINDOW,
                                     lambda x: self.id_column_checkbox.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.id_column_checkbox.Hide()

        self.statictext_increment_start = wx.StaticText(id_column_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.TABLE_PAGE.INIT_VALUE_ID'])
        id_column_boxsizer.Add(self.statictext_increment_start, 0, wx.TOP | wx.RIGHT | wx.LEFT, 5)
        self.statictext_increment_start.Hide()

        self.textctrl_increment_start = wx.TextCtrl(id_column_panel, size=(100, -1))
        self.textctrl_increment_start.SetValue('1')
        id_column_boxsizer.Add(self.textctrl_increment_start, 0, wx.LEFT, 5)
        self.textctrl_increment_start.Hide()

        table_page_boxsizer.Add(id_column_panel, 0, wx.TOP | wx.EXPAND, 5)
        # ----------------------------------------

        # ------------------------------
        notebook_settings.AddPage(table_page_panel, APP_TEXT_LABELS['MAIN.MAIN_PANEL.TABLE_PAGE'])
        # ------------------------------

        # Индексы
        # ------------------------------
        self.indexes_page_panel = wx.Panel(notebook_settings)
        self.indexes_page_sizer = wx.BoxSizer(wx.VERTICAL)
        self.indexes_page_panel.SetSizer(self.indexes_page_sizer)

        self.button_new_index = wx.Button(self.indexes_page_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.INDEX_PAGE.NEW_INDEX'], style=wx.NO_BORDER)
        self.button_new_index.SetBitmapLabel(wx.Bitmap("img/16x16/plus.png", wx.BITMAP_TYPE_PNG))
        self.button_new_index.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.button_new_index.Bind(wx.EVT_ENTER_WINDOW,
                                   lambda x: self.button_new_index.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.button_new_index.Bind(wx.EVT_BUTTON, create_index)
        self.indexes_page_sizer.Add(self.button_new_index, 0, wx.ALL, 5)

        self.indexes_page_sizer.Add(wx.StaticLine(self.indexes_page_panel), 0,
                                    wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 0)

        # ----------------------------------------

        self.indexes_scrolledwindow = wx.lib.scrolledpanel.ScrolledPanel(self.indexes_page_panel, size=(-1, 1000))
        self.indexes_scrolledwindow.SetupScrolling()
        self.indexes_scrolledwindow.SetAutoLayout(1)
        self.indexes_sizer = wx.BoxSizer(wx.VERTICAL)
        self.indexes_scrolledwindow.SetSizer(self.indexes_sizer)
        # ----------------------------------------
        self.indexes_page_sizer.Add(self.indexes_scrolledwindow, 0, wx.EXPAND)
        # ------------------------------
        notebook_settings.AddPage(self.indexes_page_panel, APP_TEXT_LABELS['MAIN.MAIN_PANEL.INDEX_PAGE'])
        # --------------------

        # Редактор кода
        self.textctrl_sql = wx.stc.StyledTextCtrl(table_panel, style=wx.TE_MULTILINE)
        stc_redactors.append(self.textctrl_sql)
        # Установка стилей
        self.stc_reset_style(self.textctrl_sql)
        # -------------------
        table_panel.SplitHorizontally(notebook_settings, self.textctrl_sql)
        table_panel.SetMinimumPaneSize(100)
        # -------------------
        data_panel.SplitVertically(self.treectrl_databases, table_panel, 150)
        data_panel.SetMinimumPaneSize(150)
        main_boxsizer.Add(data_panel, 1, wx.BOTTOM | wx.EXPAND)
        # ----------

        self.statusbar = self.CreateStatusBar(1, wx.STB_ELLIPSIZE_END)
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusText(self.query_status, 0)

        main_panel.Layout()
        main_panel.Show()


class AboutApp(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['MAIN.MAIN_MENU.INFO.ABOUT_APP'], size=(350, 250),
                          style=wx.CAPTION | wx.CLOSE_BOX)
        self.SetMinSize((350, 250))
        self.SetMaxSize((350, 250))
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(self.sizer)

        # ----------

        self.info_panel = wx.Panel(self.panel)
        self.info_sizer = wx.BoxSizer(wx.VERTICAL)
        self.info_panel.SetSizer(self.info_sizer)

        info_image = wx.Image('img/SDForge.png', wx.BITMAP_TYPE_PNG)
        info_image.Rescale(200, 90, wx.IMAGE_QUALITY_BOX_AVERAGE)
        image_bitmap = wx.StaticBitmap(self.info_panel, -1, wx.BitmapFromImage(info_image))
        self.info_sizer.Add(image_bitmap, 0)

        self.info_sizer.AddMany([(wx.StaticText(self.info_panel, label='SDForge v.1.5.0, 2024'), 0, wx.TOP, 10),
                                 (wx.StaticText(self.info_panel, label='QWerProg - Дмитрий Степанов'), 0, wx.TOP, 10),
                                 (wx.StaticText(self.info_panel, label='ds.qwerprog04@mail.ru'), 0)])

        self.sizer.Add(self.info_panel, 0, wx.ALL, 20)
        # ----------

        self.buttons_panel = wx.Panel(self.panel)
        self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.ok_button = wx.Button(self.buttons_panel, label='OK', size=(75, -1))
        self.ok_button.Bind(wx.EVT_BUTTON, lambda x: self.Destroy())
        self.ok_button.SetFocus()
        self.buttons_sizer.Add(self.ok_button, 0, wx.BOTTOM, 5)

        self.github_button = wx.Button(self.buttons_panel, label='GitHub', size=(75, -1))
        self.github_button.Bind(wx.EVT_BUTTON, lambda x: webbrowser.open('https://github.com/QWerProd/SQLDataForge'))
        self.buttons_sizer.Add(self.github_button, 0, wx.BOTTOM, 5)

        self.sizer.Add(self.buttons_panel, 0, wx.TOP | wx.RIGHT, 20)
        # ----------

        self.Layout()


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
