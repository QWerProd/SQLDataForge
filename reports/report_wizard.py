import wx
import os
import wx.lib.mixins.listctrl
from datetime import datetime

from data_controller import DataController
from reports.report_generator import ReportGenerator
from app_parameters import APP_TEXT_LABELS, APPLICATION_PATH, APP_PARAMETERS


class ReportWizard(wx.Frame):

    curr_page = int
    curr_page_panel = wx.Panel
    pages = list

    class ChooseColumns(wx.Panel):

        columns = list
        columns_text = list
        databases = list
        tree_items = dict
        all_tables = dict

        def set_databases_tree_items(self):
            for key, value in self.all_tables.items():
                temp_items = []
                udb_name_label = ''
                if APP_PARAMETERS['IS_ALIAS_UDB_USING'] == 'True':
                    for db_info in self.databases:
                        if db_info[0] == key:
                            udb_name_label = db_info[1]
                            break
                else:
                    udb_name_label = key
                root = self.treectrl_columns.AppendItem(self.treectrl_columns_root, udb_name_label)
                if len(value) > 0:
                    self.treectrl_columns.SetItemImage(root, self.database_image)
                    for full_item in value:
                        item = full_item.split(':')[2]
                        child = self.treectrl_columns.AppendItem(root, item)
                        self.treectrl_columns.SetItemImage(child, self.table_image)
                        temp_items.append(child)
                    self.tree_items[root] = temp_items
                else:
                    self.treectrl_columns.SetItemImage(root, self.invalid_db_image)

        def on_treeitem_activated(self, event):
            get_item = event.GetItem()
            activated = self.treectrl_columns.GetItemText(get_item)
            if not activated.endswith('.db'):
                is_appended = False
                for key, value in self.all_tables.items():
                    for colinfo in value:
                        if activated in colinfo:
                            is_appended = True
                            add_col = f'{key}:{colinfo}'
                            if len(self.columns) <= 0 or add_col not in self.columns:
                                self.columns.append(add_col)
                                self.columns_text.append(add_col.split(':')[3])
                                self.treectrl_columns.SetItemBold(get_item, True)
                            else:
                                self.columns.remove(add_col)
                                self.columns_text.remove(add_col.split(':')[3])
                                self.treectrl_columns.SetItemBold(get_item, False)
                            break
                    if is_appended:
                        break
                self.items_listbox.SetItems(self.columns_text)

        def get_columns_info(self) -> list: return self.columns

        def get_rows_count(self) -> int: return int(self.row_count_entry.GetValue())

        def clear_form(self, event):
            self.columns.clear()
            self.columns_text.clear()
            for items in self.tree_items.values():
                for item in items:
                    self.treectrl_columns.SetItemBold(item, False)
            self.items_listbox.Clear()
            self.row_count_entry.SetValue('1')

        def __init__(self, parent: wx.Window):
            super().__init__(parent)
            self.databases = DataController.GetDatabases(False)
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.tree_items = {}
            self.columns = []
            self.columns_text = []
            self.SetSizer(self.sizer)

            title_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_COLUMNS.TITLE'])
            self.sizer.Add(title_statictext, 0, wx.LEFT | wx.TOP | wx.RIGHT, 20)

            # ----------

            div_horizontal_panel = wx.Panel(self)
            div_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
            div_horizontal_panel.SetSizer(div_horizontal_sizer)

            self.treectrl_columns = wx.TreeCtrl(div_horizontal_panel,
                                                style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT)
            self.treectrl_columns_root = self.treectrl_columns.AddRoot('')
            self.all_tables = DataController.GetTablesFromDB()
            self.image_database_items = wx.ImageList(16, 16)
            self.database_image = self.image_database_items.Add(
                wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/database.png'),
                         wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            self.invalid_db_image = self.image_database_items.Add(
                wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/delete database.png'),
                         wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            self.table_image = self.image_database_items.Add(
                wx.Image(os.path.join(APPLICATION_PATH, 'img/16x16/table.png'),
                         wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            self.treectrl_columns.AssignImageList(self.image_database_items)
            self.set_databases_tree_items()
            self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_treeitem_activated, self.treectrl_columns)
            div_horizontal_sizer.Add(self.treectrl_columns, 1, wx.EXPAND | wx.TOP, 5)

            # --------------------

            buttons_panel = wx.Panel(div_horizontal_panel)
            buttons_sizer = wx.BoxSizer(wx.VERTICAL)
            buttons_panel.SetSizer(buttons_sizer)

            self.clear_button = wx.BitmapButton(buttons_panel, style=wx.NO_BORDER,
                                                bitmap=wx.BitmapBundle(wx.Bitmap(os.path.join(APPLICATION_PATH, 'img/16x16/recycle bin sign.png'))))
            self.clear_button.Bind(wx.EVT_ENTER_WINDOW, lambda evt: self.clear_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            self.clear_button.Bind(wx.EVT_BUTTON, self.clear_form)
            buttons_sizer.Add(self.clear_button, 0, wx.ALL, 5)

            div_horizontal_sizer.Add(buttons_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 5)
            # --------------------

            self.items_listbox = wx.ListBox(div_horizontal_panel)
            div_horizontal_sizer.Add(self.items_listbox, 1, wx.EXPAND | wx.TOP, 5)

            self.sizer.Add(div_horizontal_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
            # ----------

            div_row_count_panel = wx.Panel(self)
            div_row_count_sizer = wx.BoxSizer(wx.HORIZONTAL)
            div_row_count_panel.SetSizer(div_row_count_sizer)

            row_count_statictext = wx.StaticText(div_row_count_panel, label=APP_TEXT_LABELS['MAIN.MAIN_PANEL.MAIN_PAGE.ROW_COUNT'])
            div_row_count_sizer.Add(row_count_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP, 5)

            self.row_count_entry = wx.TextCtrl(div_row_count_panel, value='1')
            div_row_count_sizer.Add(self.row_count_entry, 1, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 5)

            self.sizer.Add(div_row_count_panel, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)
            # ----------

            self.Layout()

    class ChooseReportType(wx.Panel):

        file_path = str
        file_extensions = ('XLSX', 'CSV', 'DOCX')
        curr_extension = str
        file_templates = {
            'XLSX': os.path.join(APPLICATION_PATH, 'reports/templates/template.xlsx'),
            'CSV': os.path.join(APPLICATION_PATH, 'reports/templates/'),
            'DOCX': None
        }
        file_wildcards = {
            'XLSX': APP_TEXT_LABELS['FILE_DIALOG.WILDCARD_XLSX'],
            'DOCX': APP_TEXT_LABELS['FILE_DIALOG.WILDCARD_DOCX']
        }
        template_path = str
        template_name = str

        def explore_path(self, event):
            with wx.DirDialog(None, APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DIR_DIALOG'], 
                              defaultPath=APP_PARAMETERS['PATH_FOR_REPORTS']) as dir_dialog:
                if dir_dialog.ShowModal() == wx.ID_CANCEL:
                    return

                self.file_path = dir_dialog.GetPath()
                self.file_path_textctrl.SetValue(self.file_path)

        def change_extension(self, event):
            self.curr_extension = self.file_extensions[self.file_extension_radiobox.GetSelection()]
            self.set_template_name()

        def set_template_name(self):
            file_path = self.file_templates[self.curr_extension]
            if file_path is None:
                file_name = '...'
                self.template_name = ''
                self.set_template_button.Enable()
                self.set_template_button.SetFocus()
            else:
                file_name = os.path.basename(file_path)
                self.template_name = file_name
                if file_name == '':
                    file_name = '...'
                    self.set_template_button.Disable()
            self.template_path = file_path
            self.template_statictext.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME'] + f' {file_name}')

        def set_file_template(self, event):
            wildcards = self.file_wildcards[self.curr_extension]
            with wx.FileDialog(None, APP_TEXT_LABELS['FILE_DIALOG.CAPTION_CHOOSE'],
                               wildcard=wildcards) as dir_dialog:
                if dir_dialog.ShowModal() == wx.ID_CANCEL:
                    return

                self.template_path = dir_dialog.GetPath()
                self.template_name = dir_dialog.GetFilename()

            self.template_statictext.SetLabel(APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME'] + f' {self.template_name}')

        def get_template_info(self) -> (str, str): return self.template_name, self.template_path

        def get_file_info(self) -> (str, str, str):
            return (self.file_name_textctrl.GetValue() + '.' + self.curr_extension.lower(),
                    self.file_path, self.curr_extension.lower())

        def get_report_info(self) -> dict:
            info = {'report-name': self.report_name_textctrl.GetValue(),
                    'report-date': datetime.now().strftime('%d.%m.%Y')}
            return info

        def __init__(self, parent: wx.Window):
            super().__init__(parent)
            self.template_path = ''
            self.template_name = ''
            self.file_path = ''
            self.curr_extension = self.file_extensions[0]
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            title_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.TITLE'])
            self.sizer.Add(title_statictext, 0, wx.LEFT | wx.TOP | wx.RIGHT, 20)

            # ----------

            file_info_panel = wx.Panel(self)
            file_info_staticbox = wx.StaticBox(file_info_panel,
                                               label=APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_TITLE'])
            file_info_sizer = wx.StaticBoxSizer(file_info_staticbox, wx.VERTICAL)
            file_info_panel.SetSizer(file_info_sizer)

            # --------------------

            file_name_panel = wx.Panel(file_info_panel)
            file_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            file_name_panel.SetSizer(file_name_sizer)

            file_name_statictext = wx.StaticText(file_name_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME'], size=(100, -1))
            file_name_sizer.Add(file_name_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

            self.file_name_textctrl = wx.TextCtrl(file_name_panel, size=(-1, 22))
            file_name_sizer.Add(self.file_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            file_info_sizer.Add(file_name_panel, 0, wx.ALL | wx.EXPAND, 5)
            # --------------------

            file_path_panel = wx.Panel(file_info_panel)
            file_path_sizer = wx.BoxSizer(wx.HORIZONTAL)
            file_path_panel.SetSizer(file_path_sizer)

            file_path_statictext = wx.StaticText(file_path_panel, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DB_PATH'], size=(100, -1))
            file_path_sizer.Add(file_path_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.file_path_textctrl = wx.TextCtrl(file_path_panel, size=(-1, 22))
            file_path_sizer.Add(self.file_path_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            self.explore_path_button = wx.Button(file_path_panel, label='...', size=(25, 24), style=wx.NO_BORDER)
            self.explore_path_button.Bind(wx.EVT_ENTER_WINDOW,
                                          lambda x: self.explore_path_button.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
            self.explore_path_button.Bind(wx.EVT_BUTTON, self.explore_path)
            file_path_sizer.Add(self.explore_path_button, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

            file_info_sizer.Add(file_path_panel, 0, wx.LEFT | wx.BOTTOM | wx.RIGHT | wx.EXPAND, 5)
            # --------------------

            self.sizer.Add(file_info_panel, 0, wx.ALL | wx.EXPAND, 20)
            # ----------

            div_horizontal_panel = wx.Panel(self)
            div_horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
            div_horizontal_panel.SetSizer(div_horizontal_sizer)

            self.file_extension_radiobox = wx.RadioBox(div_horizontal_panel, label=APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.FILE_EXTENSION'],
                                                       choices=list(map(lambda x: x + ' file', self.file_extensions)),
                                                       style=wx.RA_SPECIFY_ROWS)
            self.file_extension_radiobox.Bind(wx.EVT_RADIOBOX, self.change_extension)
            div_horizontal_sizer.Add(self.file_extension_radiobox)

            # --------------------

            div_vertical_panel = wx.Panel(div_horizontal_panel)
            div_vertical_sizer = wx.BoxSizer(wx.VERTICAL)
            div_vertical_panel.SetSizer(div_vertical_sizer)

            # ------------------------------

            template_panel = wx.Panel(div_vertical_panel)
            template_box = wx.StaticBox(template_panel, label=APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.FILE_TEMPLATE'])
            template_sizer = wx.StaticBoxSizer(template_box, wx.VERTICAL)
            template_panel.SetSizer(template_sizer)

            self.template_statictext = wx.StaticText(template_panel)
            self.set_template_name()
            template_sizer.Add(self.template_statictext, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 5)

            self.set_template_button = wx.Button(template_panel, label=APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.FILE_TEMPLATE.CHANGE'])
            self.set_template_button.Bind(wx.EVT_BUTTON, self.set_file_template)
            template_sizer.Add(self.set_template_button, 0, wx.LEFT | wx.BOTTOM, 5)

            div_vertical_sizer.Add(template_panel, 0, wx.EXPAND | wx.BOTTOM, 20)
            # ------------------------------

            other_parameters_panel = wx.Panel(div_vertical_panel)
            other_parameters_box = wx.StaticBox(other_parameters_panel, label=APP_TEXT_LABELS['APP.SETTINGS.SYSTEM.PARAMETERS'] + ':')
            other_parameters_sizer = wx.StaticBoxSizer(other_parameters_box, wx.VERTICAL)
            other_parameters_panel.SetSizer(other_parameters_sizer)

            # ----------------------------------------

            report_name_panel = wx.Panel(other_parameters_panel)
            report_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            report_name_panel.SetSizer(report_name_sizer)

            report_name_statictext = wx.StaticText(report_name_panel, label=APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.PARAMETERS.REPORT_NAME'])
            report_name_sizer.Add(report_name_statictext, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.report_name_textctrl = wx.TextCtrl(report_name_panel, size=(-1, 22))
            report_name_sizer.Add(self.report_name_textctrl, 1, wx.ALIGN_CENTER_VERTICAL)

            other_parameters_sizer.Add(report_name_panel, 0, wx.ALL | wx.EXPAND, 5)
            # ----------------------------------------

            div_vertical_sizer.Add(other_parameters_panel, 0, wx.EXPAND)
            # ------------------------------

            div_horizontal_sizer.Add(div_vertical_panel, 1, wx.EXPAND | wx.LEFT, 20)
            # --------------------

            self.sizer.Add(div_horizontal_panel, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)
            # ----------

            self.Layout()

    class FinishInfo(wx.Panel):

        added_items = list
        row_count = int
        file_extension = str
        template_name = str
        template_path = str
        file_name = str
        file_path = str
        report_info = dict

        def set_added_items(self, items: list): self.added_items = items

        def set_rows_count(self, count: int): self.row_count = count

        def set_template(self, path: str, name: str):
            self.template_name = name
            self.template_path = path

        def set_file_info(self, name: str, path: str, extension: str):
            self.file_name = name
            self.file_path = path
            self.file_extension = extension

        def set_report_info(self, info: dict): self.report_info = info

        def set_textctrl_value(self):
            text = (f'Информация об отчете:\n'
                    f'    Имя отчета: {self.report_info["report-name"]}\n'
                    f'    Расположение файла: {os.path.join(self.file_path, self.file_name)}\n'
                    f'\n'
                    f'    Выбранные столбцы: {", ".join(list(map(lambda x: x.split(":")[3], self.added_items)))}')
            self.info_textctrl.SetValue(text)

        def __init__(self, parent: wx.Window):
            super().__init__(parent)
            self.added_items = []
            self.row_count = 0
            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)

            title_statictext = wx.StaticText(self, label=APP_TEXT_LABELS['NEW_UDB_WIZARD.THIRD_PAGE.INFO_CHECK'])
            self.sizer.Add(title_statictext, 0, wx.ALL, 20)

            self.info_textctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)
            self.sizer.Add(self.info_textctrl, 1, wx.ALL | wx.EXPAND, 10)

            self.Layout()

    # --------------------------------------------------

    def cancel(self, event):
        dlg = wx.MessageBox(APP_TEXT_LABELS['NEW_UDB_WIZARD.CANCEL_MESSAGE.MESSAGE'],
                            APP_TEXT_LABELS['MESSAGE_BOX.CAPTION_APPROVE'], wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if dlg == wx.YES:
            self.Destroy()

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
            try:
                row_count = self.curr_page_panel.get_rows_count()
            except ValueError:
                return wx.MessageBox(APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_COLUMN.INVALID_ROWCOUNT.MESSAGE'],
                                     APP_TEXT_LABELS['SINGLE_GENERATOR.MESSAGE_BOX.ERROR_GENERATE.CAPTION'],
                                     wx.ICON_ERROR | wx.OK_DEFAULT)
            added_items = self.curr_page_panel.get_columns_info()
            if len(added_items) == 0:
                return wx.MessageBox(APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_COLUMN.NONE_COLUMNS.MESSAGE'],
                                     APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_COLUMN.NONE_COLUMNS.CAPTION'],
                                     wx.ICON_WARNING | wx.OK_DEFAULT)
            elif int(row_count) <= 0:
                return wx.MessageBox(APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_COLUMN.INVALID_ROWCOUNT.MESSAGE'],
                                     APP_TEXT_LABELS['SINGLE_GENERATOR.MESSAGE_BOX.ERROR_GENERATE.CAPTION'],
                                     wx.ICON_ERROR | wx.OK_DEFAULT)
            next_page = self.type_report_page
            self.finish_panel.set_rows_count(row_count)
            self.finish_panel.set_added_items(added_items)
        elif self.curr_page == 1:
            file_name, file_path, file_extension = self.curr_page_panel.get_file_info()
            template_name, template_path = self.curr_page_panel.get_template_info()
            report_info = self.curr_page_panel.get_report_info()
            if file_name == '' or (file_path == '' or not os.path.exists(file_path)):
                return wx.MessageBox(APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.NULL_FILE_INFO.MESSAGE'],
                                     APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.NULL_FILE_INFO.CAPTION'],
                                     wx.ICON_ERROR | wx.OK_DEFAULT)
            if file_extension not in ('CSV',) and (template_name == '' and (template_path in ('', None) or not os.path.exists(template_path))):
                return wx.MessageBox(APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.NULL_TEMPLATE_INFO.MESSAGE'],
                                     APP_TEXT_LABELS['REPORT_WIZARD.CHOOSE_TYPE.NULL_TEMPLATE_INFO.CAPTION'],
                                     wx.ICON_ERROR | wx.OK_DEFAULT)
            next_page = self.finish_panel
            if not file_name.endswith('.' + file_extension.lower()):
                file_name += '.' + file_extension.lower()
            self.finish_panel.set_file_info(file_name, file_path, file_extension)
            self.finish_panel.set_template(template_path, template_name)
            self.finish_panel.set_report_info(report_info)
            self.finish_panel.set_textctrl_value()
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
        file_name, file_path, file_extension = self.type_report_page.get_file_info()
        template_name, template_path = self.type_report_page.get_template_info()
        report_info = self.type_report_page.get_report_info()
        reports = ReportGenerator(self.init_page.get_rows_count(), self.init_page.get_columns_info(), file_name, file_path,
                                  report_info, template_name, template_path)

        result = False
        if file_extension == 'csv':
            result = reports.build_csv()
        elif file_extension == 'docx':
            result = reports.build_docx()
        elif file_extension == 'xlsx':
            result = reports.build_xlsx()

        if result:
            wx.MessageBox(APP_TEXT_LABELS['REPORT_WIZARD.REPORT_SAVED.MESSAGE'].format(report_info['report-name'], os.path.join(file_path, file_name)),
                          APP_TEXT_LABELS['REPORT_WIZARD.REPORT_SAVED.CAPTION'],
                          wx.ICON_INFORMATION | wx.OK_DEFAULT)
            if APP_PARAMETERS['IS_CLOSING_REPORTS_AFTER_GEN'] == 'True':
                self.Destroy()

    def __init__(self):
        wx.Frame.__init__(self, None, size=(800, 500), title=APP_TEXT_LABELS['REPORT_WIZARD.TITLE'],
                          style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MINIMIZE_BOX)
        self.SetMinSize((800, 500))
        self.SetMaxSize((1000, 600))
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.curr_page = 0
        self.pages = []

        self.small_header_font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        # ---------

        header_panel = wx.Panel(self.panel)
        header_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_panel.SetSizer(header_sizer)

        header_image = wx.Image(os.path.join(APPLICATION_PATH, 'img/32x32/report.png'), wx.BITMAP_TYPE_PNG)
        header_bitmap = wx.StaticBitmap(header_panel, bitmap=wx.BitmapFromImage(header_image))
        header_sizer.Add(header_bitmap, 0, wx.ALL, 10)

        # --------------------

        header_info_panel = wx.Panel(header_panel)
        header_info_sizer = wx.BoxSizer(wx.VERTICAL)
        header_info_panel.SetSizer(header_info_sizer)

        info_header_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['REPORT_WIZARD.TITLE'])
        info_header_statictext.SetFont(self.small_header_font)
        header_info_sizer.Add(info_header_statictext, 0, wx.ALL)

        info_data_statictext = wx.StaticText(header_info_panel, label=APP_TEXT_LABELS['REPORT_WIZARD.HEADER2'])
        header_info_sizer.Add(info_data_statictext, 0, wx.ALL)

        header_sizer.Add(header_info_panel, 0, wx.ALL, 10)
        # --------------------

        self.sizer.Add(header_panel, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND)
        # ----------

        self.main_panel = wx.Panel(self.panel)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(self.main_sizer)

        self.init_page = ReportWizard.ChooseColumns(self.main_panel)
        self.main_sizer.Add(self.init_page, 1, wx.EXPAND)
        self.type_report_page = ReportWizard.ChooseReportType(self.main_panel)
        self.main_sizer.Add(self.type_report_page, 1, wx.EXPAND)
        self.type_report_page.Hide()
        self.finish_panel = ReportWizard.FinishInfo(self.main_panel)
        self.main_sizer.Add(self.finish_panel, 1, wx.EXPAND)
        self.finish_panel.Hide()

        self.curr_page_panel = self.init_page

        self.sizer.Add(self.main_panel, 1, wx.EXPAND)
        # ----------

        div_separator_panel = wx.Panel(self.panel)
        div_separator_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_separator_panel.SetSizer(div_separator_sizer)

        div_separator_statictext = wx.StaticText(div_separator_panel, label='SQLDataForge: ReportWizard')
        div_separator_statictext.SetForegroundColour(wx.Colour(150, 150, 150))
        div_separator_sizer.Add(div_separator_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        div_separator_sizer.Add(wx.StaticLine(div_separator_panel), 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.sizer.Add(div_separator_panel, 0, wx.EXPAND | wx.TOP, 5)
        # ---------

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

        self.sizer.Add(self.buttons_panel, 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)
        # ----------

        self.Layout()
