import wx
import os
import sys
import sqlite3

from app_parameters import APP_PARAMETERS, APP_TEXT_LABELS, APPLICATION_PATH
from app.error_catcher import ErrorCatcher


class UDBFillingMaster(wx.Frame):

    db_name = ''
    pdb_path = ''
    column_info = {}
    column_values = {}
    
    page_num = 0
    pages = []
    curr_page_panel: wx.Panel


    ###########################################
    ### Методы управления страницами через кнопки
    ###########################################

    def cancel(self, event):
        dialog = wx.MessageBox(APP_TEXT_LABELS['NEW_UDB_WIZARD.CANCEL_MESSAGE.MESSAGE'],
                               APP_TEXT_LABELS['MESSAGE_BOX.CAPTION_APPROVE'],
                               wx.OK | wx.CANCEL)
        if dialog == wx.CANCEL:
            return

        self.Destroy()

    def previous_page(self, event):
        # Переход назад
        self.page_num -= 1
        self.curr_page_panel.Hide()
        prev_page = self.pages[self.page_num]
        prev_page.Show()
        self.pages.remove(prev_page)
        self.curr_page_panel = prev_page

        # Манипуляции после перехода назад
        match self.page_num:
            case 0:
                self.previous_button.Disable()
                self.previous_button.Unbind(wx.EVT_ENTER_WINDOW)
            case 2:
                self.next_button.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.NEXT'])
                self.next_button.Bind(wx.EVT_BUTTON, self.next_page)

    def next_page(self, event):
        # Манипуляции перед переходом вперед
        next_page: wx.Panel
        match self.page_num:
            case 0:
                next_page = self.page2
                self.db_name = self.page1.get_db_name()
                self.page2.set_curr_db(self.db_name)
                table_list = self.page2.get_tables_list()
                max_posid = self.page2.get_max_posid()
                self.page2.table_textctrl.AutoComplete(UDBFillingMaster.ColumnInformationPage.MyClassCompleterSimple(table_list))
                self.page2.posid_spinctrl.SetValue(max_posid)
            case 1:
                self.column_info = self.curr_page_panel.get_column_info()
                self.pdb_path = self.curr_page_panel.get_pdb_path()
                match self.column_info['gen_type']:
                    case "RSet":
                        next_page = self.page3_RSet
                    case "RValue":
                        next_page = self.page3_RValue
                next_page.set_column_info(self.column_info)
            case 2:
                next_page = self.page4
                self.column_values = self.curr_page_panel.get_values()
                next_page.set_info(self.column_info, self.column_values)
                next_page.set_confirmation_info()
                
        # Переход вперед
        self.page_num += 1
        self.curr_page_panel.Hide()
        next_page.Show()
        self.pages.append(self.curr_page_panel)
        self.curr_page_panel = next_page
        self.main_panel.Layout()

        # Блокировка кнопки "Назад" на первой странице
        if self.page_num != 0:
            self.previous_button.Enable()
            self.previous_button.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.previous_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))

        # Выход на финишную страницу
        if self.page_num == 3:
            self.next_button.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.BUTTON.FINISH'])
            self.next_button.SetFocus()
            self.next_button.Bind(wx.EVT_BUTTON, self.finish)

    def finish(self, event):
        # Открываем подключение к пБД
        conn = sqlite3.connect(self.pdb_path)
        pdb_curs = conn.cursor()

        # Проверка на наличие данной таблицы
        check_table_query = f"""SELECT 1 
                                FROM sqlite_master 
                                WHERE type = 'table' 
                                AND name = '{self.column_info['table_name']}';"""
        is_created = pdb_curs.execute(check_table_query).fetchone()

        # Если таблица НЕ создана
        if is_created is None:

            # Создание таблицы со столбцами
            query_create_table = f"""CREATE TABLE "{self.column_info['table_name']}" """ 
            column_rows = []
            for key in self.column_values.keys():
                column_row = f'"{key}" TEXT'
                column_rows.append(column_row)
            query_create_table += '( "id" INTEGER NOT NULL, ' + ', '.join(column_rows) + ', PRIMARY KEY("id" AUTOINCREMENT));'
            pdb_curs.execute(query_create_table)

        # Если таблица уже существует и нужно просто добавить столбец
        else:
            for key in self.column_values.keys():
                query_create_column = f"""ALTER TABLE "{self.column_info['table_name']}" 
                                          ADD COLUMN "{key}" TEXT;"""
                pdb_curs.execute(query_create_column)

        # Обработка данных для вставки
        for key, value in self.column_values.items():

            # Сборка вертикальной матрицы значений с одной колонкой для вставки
            values = [(x,) for x in value]

            # Вставка данных
            pdb_curs.executemany(f"""INSERT INTO "{self.column_info['table_name']}" ("{key}")
                                     VALUES (?);""", values)
        
        # Запись нового столбца
        pdb_curs.execute(f"""INSERT INTO t_cases_info(posid, table_name, column_name, column_code, column_type, gen_key)
                             VALUES (?, ?, ? ,? ,? ,?)""", 
                             (self.column_info['posid'], self.column_info['table_name'], self.column_info['column_name'], 
                              self.column_info['column_code'], self.column_info['data_type'], self.column_info['gen_type']))

        conn.commit()
        pdb_curs.close()
        conn.close()

        # Завершение работы
        wx.MessageBox(APP_TEXT_LABELS['UDB_FILLING_MASTER.FINISH_MESSAGE.MESSAGE'],
                      APP_TEXT_LABELS['UDB_FILLING_MASTER.FINISH_MESSAGE.CAPTION'],
                      wx.OK_DEFAULT | wx.ICON_INFORMATION)
        self.Close()

    ###########################################
    ### Первая страница, выбор пБД
    ###########################################
    class ChooseUDBPage(wx.Panel):

        app_conn: sqlite3.Connection
        udb_list: list

        def get_db_name(self) -> str: return self.udb_combobox.GetValue()

        def update_udb_list(self, event=None):
            curs = self.app_conn.cursor()

            self.udb_list = list(map(lambda x: x[0], 
                                     curs.execute("""SELECT dbname
                                                     FROM   t_databases
                                                     WHERE  is_valid = 'Y';""").fetchall()))
            curs.close()
            self.udb_combobox.Clear()
            self.udb_combobox.Set(self.udb_list)

        def __init__(self, parent: wx.Panel, app_conn: sqlite3.Connection):
            super().__init__(parent)
            self.app_conn = app_conn
            # ------------------------------
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.CHOOSE_UDB_PAGE.HEADER'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            self.udb_combobox = wx.ComboBox(self, size=(150, -1))
            self.data_sizer.Add(self.udb_combobox, 0, wx.LEFT, 20)

            self.update_udb_list()
            self.Layout()
    

    ###########################################
    ### Вторая страница, информация о новом столбце
    ###########################################

    class ColumnInformationPage(wx.Panel):

        app_conn: sqlite3.Connection
        dbpath: str
        datatypes = ["text-value", "integer-value", "float-value", "date-value", "boolean-value"]
        generator_types = ["RSet", "RValue"]

        class MyClassCompleterSimple(wx.TextCompleterSimple):
            
            choices: list

            def __init__(self, choices: list, maxResults=25):
                wx.TextCompleterSimple.__init__(self)
                self._iMaxResults = maxResults
                self.choices = choices

            def GetCompletions(self, prefix):
                if len(prefix) < 2:
                    return []
                res = []
                prfx = prefix.lower()
                for item in self.choices:
                    if item.lower().startswith(prfx):
                        res.append(item)
                        if len(res) == self._iMaxResults:
                            return res

                return res
            
        def set_curr_db(self, db_name: str): 
            pdb_curs = self.app_conn.cursor()
            self.dbpath = pdb_curs.execute("""SELECT path
                                              FROM   t_databases
                                              WHERE  dbname = ?""", (db_name,)).fetchone()[0]
            pdb_curs.close()
        
        def get_tables_list(self) -> list:
            tables_list = []
            with sqlite3.connect(self.dbpath) as conn:
                curs = conn.cursor()
                tables_list = list(map(lambda x: x[0], curs.execute("""SELECT DISTINCT table_name
                                                                       FROM t_cases_info
                                                                       WHERE gen_key NOT IN ('RChain', 'RValue', 'RDate')
                                                                       UNION
                                                                       SELECT name
                                                                       FROM sqlite_master
                                                                       WHERE type = 'table'
																	   AND name NOT IN ('t_cases_info', 'sqlite_sequence');""").fetchall()))
                curs.close()
            return tables_list
        
        def get_max_posid(self) -> int:
            max_posid = 0
            with sqlite3.connect(self.dbpath) as conn:
                curs = conn.cursor()
                max_posid = int(curs.execute("""SELECT COALESCE((MAX(posid) + 1), '1') FROM t_cases_info""").fetchone()[0])
                curs.close()

            return max_posid
        
        def get_column_info(self) -> dict:
            column_info = {}
            column_info['table_name'] = self.table_textctrl.GetValue()
            column_info['column_name'] = self.column_name_textctrl.GetValue()
            column_info['column_code'] = self.column_code_textctrl.GetValue()
            column_info['posid'] = str(self.posid_spinctrl.GetValue())
            column_info['data_type'] = self.datatype_combobox.GetValue()
            column_info['gen_type'] = self.generator_type_combobox.GetValue()
            return column_info
        
        def get_pdb_path(self) -> str: return self.dbpath

        def __init__(self, parent: wx.Panel, app_conn: sqlite3.Connection):
            super().__init__(parent)
            self.app_conn = app_conn
            # ------------------------------
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.COLUMN_INFORMATION.HEADER'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            # ----------------------------------------
            self.column_info_panel = wx.Panel(self)
            column_info_staticbox = wx.StaticBox(self.column_info_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.COLUMN_INFORMATION'])
            self.column_info_sizer = wx.StaticBoxSizer(column_info_staticbox, wx.VERTICAL)
            self.column_info_panel.SetSizer(self.column_info_sizer)

            # --------------------------------------------------

            self.first_row_panel = wx.Panel(self.column_info_panel)
            self.first_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.first_row_panel.SetSizer(self.first_row_sizer)

            table_statictext = wx.StaticText(self.first_row_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE.TABLE_NAME'])
            self.first_row_sizer.Add(table_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.table_textctrl = wx.TextCtrl(self.first_row_panel)
            self.first_row_sizer.Add(self.table_textctrl, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

            column_name_statictext = wx.StaticText(self.first_row_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.COLUMN_INFORMATION.COLUMN_NAME'])
            self.first_row_sizer.Add(column_name_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.column_name_textctrl = wx.TextCtrl(self.first_row_panel)
            self.first_row_sizer.Add(self.column_name_textctrl, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

            column_code_statictext = wx.StaticText(self.first_row_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.COLUMN_INFORMATION.COLUMN_CODE'])
            self.first_row_sizer.Add(column_code_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.column_code_textctrl = wx.TextCtrl(self.first_row_panel)
            self.first_row_sizer.Add(self.column_code_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)
            
            self.column_info_sizer.Add(self.first_row_panel, 1, wx.ALL | wx.EXPAND, 5)
            # --------------------------------------------------

            self.second_row_panel = wx.Panel(self.column_info_panel)
            self.second_row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.second_row_panel.SetSizer(self.second_row_sizer)

            posid_statictext = wx.StaticText(self.second_row_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.COLUMN_POSID'])
            self.second_row_sizer.Add(posid_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.posid_spinctrl = wx.SpinCtrl(self.second_row_panel, min=1, initial=1)
            self.second_row_sizer.Add(self.posid_spinctrl, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

            datatype_statictext = wx.StaticText(self.second_row_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.COLUMN_DATATYPE'])
            self.second_row_sizer.Add(datatype_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.datatype_combobox = wx.ComboBox(self.second_row_panel, choices=self.datatypes)
            self.second_row_sizer.Add(self.datatype_combobox, 2, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

            generator_type_statictext = wx.StaticText(self.second_row_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.GENERATOR_TYPE'])
            self.second_row_sizer.Add(generator_type_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.generator_type_combobox = wx.ComboBox(self.second_row_panel, choices=self.generator_types)
            self.second_row_sizer.Add(self.generator_type_combobox, 2, wx.ALIGN_CENTER_VERTICAL)

            self.column_info_sizer.Add(self.second_row_panel, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
            # --------------------------------------------------

            self.data_sizer.Add(self.column_info_panel, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)
            # ----------------------------------------

            self.Layout()
    

    ###########################################
    ### Третья страница, заполнение для RSet
    ###########################################

    class RSetFillerPage(wx.Panel):

        app_conn: sqlite3.Connection
        column_info: dict

        def set_column_info(self, column_info: dict): self.column_info = column_info

        def get_values(self) -> dict:
            column_values = {}
            text = self.values_textctrl.GetValue()
            column_values[self.column_info['column_name']] = text.split('\n')
            return column_values

        def __init__(self, parent: wx.Panel, app_conn: sqlite3.Connection = None):
            super().__init__(parent)
            self.app_conn = app_conn
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.RSET_PAGE.HEADER'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            self.values_textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE)
            self.data_sizer.Add(self.values_textctrl, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 20)

            self.Layout()
    

    ###########################################
    ### Третья страница, заполнение для RValue
    ###########################################

    class RValueFillerPage(wx.Panel):

        app_conn: sqlite3.Connection
        column_info: dict

        def set_column_info(self, column_info: dict): self.column_info = column_info

        def get_values(self) -> dict:
            column_values = {}
            minvalue = str(self.minvalue_spinctrl.GetValue())
            maxvalue = str(self.maxvalue_spinctrl.GetValue())
            column_values['min_value'] = [minvalue,]
            column_values['max_value'] = [maxvalue,]
            return column_values

        def __init__(self, parent: wx.Panel, app_conn: sqlite3.Connection = None):
            super().__init__(parent)
            self.app_conn = app_conn
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.RVALUE_PAGE.HEADER'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            # ------------------------------
            self.input_panel = wx.Panel(self)
            self.input_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.input_panel.SetSizer(self.input_sizer)

            minvalue_statictext = wx.StaticText(self.input_panel, label=APP_TEXT_LABELS['APP.SIMPLE_GEN.RAND_NUMBER.MINVALUE'])
            self.input_sizer.Add(minvalue_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.minvalue_spinctrl = wx.SpinCtrl(self.input_panel, min=-sys.maxsize, max=sys.maxsize)
            self.input_sizer.Add(self.minvalue_spinctrl, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

            maxvalue_statictext = wx.StaticText(self.input_panel, label=APP_TEXT_LABELS['APP.SIMPLE_GEN.RAND_NUMBER.MAXVALUE'])
            self.input_sizer.Add(maxvalue_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.maxvalue_spinctrl = wx.SpinCtrl(self.input_panel, min=-sys.maxsize, max=sys.maxsize, initial=1)
            self.input_sizer.Add(self.maxvalue_spinctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.data_sizer.Add(self.input_panel, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)
            # ------------------------------

            self.Layout()


    ###########################################
    ### Четвертая страница, подтверждение данных
    ###########################################

    class ConfirmationPage(wx.Panel):

        app_conn: sqlite3.Connection
        column_info: dict
        column_values: dict

        def set_info(self, column_info: dict, column_values: dict):
            self.column_info = column_info
            self.column_values = column_values

        def set_confirmation_info(self):
            text = (f"Информация о столбце:\n" +
                    f"    Имя таблицы: {self.column_info['table_name']}\n" +
                    f"    Имя столбца в таблице: {self.column_info['column_name']}\n" +
                    f"    Псевдоним столбца: {self.column_info['column_code']}\n" +
                    f"    Последовательность: {self.column_info['posid']}\n" +
                    f"    Тип данных: {self.column_info['data_type']}\n" +
                    f"    Тип генератора: {self.column_info['gen_type']}\n\n" +
                    f"Добавляемые данные:\n")
            
            for key, value in self.column_values.items():
                text_row = f"    {key}: {', '.join(value)}\n"
                text += text_row

            self.information_textctrl.SetValue(text)

        def __init__(self, parent: wx.Panel, app_conn: sqlite3.Connection):
            super().__init__(parent)
            self.app_conn = app_conn
            # --------------------
            self.data_sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.data_sizer)

            header_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_CHECK'])
            self.data_sizer.Add(header_statictext, 0, wx.ALL, 20)

            self.information_textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NO_VSCROLL)
            self.data_sizer.Add(self.information_textctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

            self.Layout()


    ###########################################
    ### Инициализация мастера
    ###########################################

    def __init__(self, catcher: ErrorCatcher):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['UDB_FILLING_MASTER.TITLE'], size=(800, 550),
                         style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MINIMIZE_BOX)
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.SetMinSize((800, 550))
        self.SetMaxSize((1000, 600))

        self.catcher = catcher
        self.app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))

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

        header_image = wx.Image(os.path.join(APPLICATION_PATH, 'img/32x32/import.png'), wx.BITMAP_TYPE_PNG)
        header_bitmap = wx.StaticBitmap(header_panel, bitmap=wx.BitmapFromImage(header_image))
        header_sizer.Add(header_bitmap, 0, wx.ALL, 10)

        # ------------------------------

        header_info_panel = wx.Panel(header_panel)
        header_info_sizer = wx.BoxSizer(wx.VERTICAL)
        header_info_panel.SetSizer(header_info_sizer)

        info_header_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.TITLE'])
        info_header_statictext.SetFont(self.small_header_font)
        header_info_sizer.Add(info_header_statictext, 0, wx.ALL)

        info_data_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['UDB_FILLING_MASTER.INFORMATION'])
        header_info_sizer.Add(info_data_statictext, 0, wx.ALL)

        header_sizer.Add(header_info_panel, 0, wx.ALL, 10)
        # ------------------------------

        self.main_sizer.Add(header_panel, 0, wx.EXPAND)
        self.main_sizer.Add(wx.StaticLine(self.main_panel), 0, wx.EXPAND)
        # ---------------

        self.main_data_panel = wx.Panel(self.main_panel)
        self.main_data_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_data_panel.SetSizer(self.main_data_sizer)

        self.page1 = self.ChooseUDBPage(self.main_data_panel, self.app_conn)
        self.curr_page_panel = self.page1

        self.page2 = self.ColumnInformationPage(self.main_data_panel, self.app_conn)
        self.page3_RSet = self.RSetFillerPage(self.main_data_panel, self.app_conn)
        self.page3_RValue = self.RValueFillerPage(self.main_data_panel, self.app_conn)
        self.page4 = self.ConfirmationPage(self.main_data_panel, self.app_conn)

        self.main_data_sizer.Add(self.page1, 0, wx.EXPAND)
        self.main_data_sizer.Add(self.page2, 0, wx.EXPAND)
        self.main_data_sizer.Add(self.page3_RSet, 1, wx.EXPAND)
        self.main_data_sizer.Add(self.page3_RValue, 0, wx.EXPAND)
        self.main_data_sizer.Add(self.page4, 1, wx.EXPAND)

        self.page2.Hide()
        self.page3_RSet.Hide()
        self.page3_RValue.Hide()
        self.page4.Hide()

        self.curr_page_panel = self.page1

        self.main_sizer.Add(self.main_data_panel, 1, wx.EXPAND)
        # --------------

        div_separator_panel = wx.Panel(self.main_panel)
        div_separator_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_separator_panel.SetSizer(div_separator_sizer)

        div_separator_statictext = wx.StaticText(div_separator_panel, label='SQLDataForge: UDBFillingWizard')
        div_separator_statictext.SetForegroundColour(wx.Colour(150, 150, 150))
        div_separator_sizer.Add(div_separator_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        div_separator_sizer.Add(wx.StaticLine(div_separator_panel), 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT, 5)

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

        self.Layout()