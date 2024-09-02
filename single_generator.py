import sqlite3
import wx
import os
import wx.stc

from data_controller import DataController
from app.error_catcher import ErrorCatcher
from app_parameters import APP_PARAMETERS, APP_TEXT_LABELS, APPLICATION_PATH
from data.simple_generators.simple_gen import (
     AcceleratorSimpleGenerator, RequiredDataMissedError, InvalidParamsError, ValidationParamsError
)
from data.simple_generators.simple_gen_inputs import (
    LabeledTextCtrl, LabeledComboBox, LabeledSpinCtrl, LabeledCheckBox, LabeledDataCtrl,
    SelectFromDB
)

# Библиотеки для генераторов
import random


class SimpleGenerator(wx.Frame):
    app_conn = sqlite3.Connection
    catcher = ErrorCatcher

    gens = DataController.BuildDictOfGens()
    items = []  # Массив с кодами генераторов
    data_items = []
    curr_data_fields = []

    open_code = str
    db_name = str

    def set_treectrl_items(self):
        root = self.items_treectrl.AddRoot('')
        for key, value in self.gens.items():
            if key == 'simple':
                second_root = self.items_treectrl.AppendItem(root, APP_TEXT_LABELS[
                    'MAIN.MAIN_MENU.GENERATOR.SIMPLE_GENERATORS'])
            else:
                second_root = self.items_treectrl.AppendItem(root, key)
            for item in value:
                treectrl_item = self.items_treectrl.AppendItem(second_root, item[1])
                self.items.append((treectrl_item, item[0]))

    def selected_item(self, event):
        item = event.GetItem()
        gen_key = None

        # Ищем полученный элемент в массиве с кодами генераторов
        for arr_item in self.items:
            if item in arr_item:
                gen_key = arr_item[1]
                break

        self.open_code = gen_key
        header_label = self.load_frame(gen_key)
        self.header_statictext.SetLabel(header_label)

    def load_frame(self, open_code=None):
        self.data_panel.DestroyChildren()
        self.curr_data_fields.clear()

        if open_code is not None:
            self.generate_button.Enable()

        if open_code is None:
            self.generate_button.Disable()
            return ''
        elif len(open_code.split(':')) == 2:
            table_name = open_code.split(':')[0]
            db_name = DataController.GetDBFromTables([table_name])

            # Возможно когда нибудь я придумаю какой интерфейс реализовать...
            try:
                entry_item = SelectFromDB(self.data_panel, db_name[0], open_code)
            except TypeError:
                self.catcher.error_message('E031')
                return None
            self.db_name = db_name[0]
            entry_item.Hide()
            # Но пока ничего такого не будет :)
            # UPD: тут будут параметры, очень не скоро
            label = entry_item.get_column_name()
            data_field_prod = wx.StaticText(self.data_panel,
                                            label=APP_TEXT_LABELS['SINGLE_GENERATOR.GO_GENERATE'] + f' \n"{label}"!')
            self.data_sizer.Add(data_field_prod, 1, wx.ALL, 50)
            self.curr_data_fields.append(entry_item)
            self.data_panel.Layout()
            self.generate_button.SetFocus()
            return label
        else:
            with sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db')) as app_conn:
                curs = app_conn.cursor()
                gen_items_info = curs.execute(f"""SELECT 
                                                    lt.text, 
                                                    se.entry_type,
                                                    lt2.text,
                                                    se.first_param,
                                                    se.second_param
                                                  FROM 
                                                    t_simple_gen_entries as se,
                                                    t_simple_gen as s,
                                                    t_lang_text as lt,
                                                    t_lang_text as lt2
                                                  WHERE se.id_field = s.id
                                                  AND   s.gen_code = '{open_code}'
                                                  AND   se.entry_name = lt.label
                                                  AND   s.gen_name = lt2.label
                                                  AND   lt.lang = '{APP_PARAMETERS['APP_LANGUAGE']}'
                                                  AND   lt2.lang = '{APP_PARAMETERS['APP_LANGUAGE']}'
                                                  ORDER BY se.posid;""").fetchall()
                curs.close()

            gen_name = ''
            addlist = []
            for item_info in gen_items_info:
                if gen_name == '':
                    gen_name = item_info[2]
                
                entry_field = None
                match item_info[1]:
                    case 'TextCtrl':
                        entry_field = LabeledTextCtrl(self.data_panel, item_info[0])
                        addlist.append([entry_field, 1, wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 15])
                    case 'ComboBox':
                        entry_field = LabeledComboBox(self.data_panel, item_info[0], str(item_info[3]).split(':'), str(item_info[4]).split(':'))
                        addlist.append([entry_field, 1, wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 15])
                    case 'SpinCtrl':
                        entry_field = LabeledSpinCtrl(self.data_panel, item_info[0], int(item_info[3]), int(item_info[4]))
                        addlist.append([entry_field, 1, wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 15])
                    case 'CheckBox':
                        entry_field = LabeledCheckBox(self.data_panel, item_info[0])
                        addlist.append([entry_field, 1, wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 15])
                    case 'DateCtrl':
                        entry_field = LabeledDataCtrl(self.data_panel, item_info[0])
                        addlist.append([entry_field, 1, wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 15])
                
                self.curr_data_fields.append(entry_field)

            self.data_sizer.AddMany(addlist)    
            self.data_panel.Layout()

            return gen_name

    def start_generate(self, event):
        count = int(self.items_count_textctrl.GetValue())

        gen_type = 'user_db' if len(self.open_code.split(':')) == 2 else 'user_input'

        params = []
        if gen_type == 'user_input':
            for data_field in self.curr_data_fields:
                value = data_field.get_value()
                params.append(value)

        # Объявление генератора и собственно генерация + обертка
        generator = AcceleratorSimpleGenerator(gen_type, self.open_code, params)

        try:
            result = generator.generate(count)
        except RequiredDataMissedError as e:
            return self.catcher.error_message('E027', str(e.args))
        except InvalidParamsError:
            return self.catcher.error_message('E028')
        except ValidationParamsError:
            return self.catcher.error_message('E029')
        
        if result is not None:
            self.output_textctrl.SetValue('\n'.join(result))

    def open_wrapper_frame(self, event):
        wrapper_frame = WrappingFrame(self, self.data_items)
        wrapper_frame.Show()
        wrapper_frame.SetFocus()

    def on_output_changed(self, event):
        text = self.output_textctrl.GetValue()
        if text != '':
            self.data_items = text.split('\n')
            if len(self.data_items) > 0:
                self.wrap_button.Enable()
            else:
                self.wrap_button.Disable()

    def __init__(self, catcher: ErrorCatcher, open_code: str = None):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['SINGLE_GENERATOR.TITLE'], size=(700, 325),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)
        self.SetIcon(wx.Icon(os.path.join(APPLICATION_PATH, 'img/main_icon.png'), wx.BITMAP_TYPE_PNG))
        self.SetMinSize((700, 325))
        self.SetMaxSize((1000, 500))
        self.app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))
        self.open_code = open_code
        self.catcher = catcher

        self.header_font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)

        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)

        # ---------------

        self.items_treectrl = wx.TreeCtrl(self.splitter,
                                          style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT)
        self.set_treectrl_items()
        self.items_treectrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.selected_item)

        # ---------------

        self.field_panel = wx.Panel(self.splitter)
        self.field_sizer = wx.BoxSizer(wx.VERTICAL)
        self.field_panel.SetSizer(self.field_sizer)

        # ------------------------------

        self.header_panel = wx.Panel(self.field_panel, style=wx.BORDER_STATIC)
        self.header_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)
        self.header_panel.SetSizer(self.header_sizer)

        self.header_statictext = wx.StaticText(self.header_panel)
        self.header_statictext.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.header_statictext.SetFont(self.header_font)
        self.header_sizer.Add(self.header_statictext, 0, wx.ALL, 5)

        self.field_sizer.Add(self.header_panel, 0, wx.EXPAND)
        # ------------------------------

        self.data_splitter = wx.SplitterWindow(self.field_panel, style=wx.SP_LIVE_UPDATE)

        # ---------------------------------------------

        self.data_panel = wx.Panel(self.data_splitter, size=(175, -1), style=wx.BORDER_STATIC)
        self.data_sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_panel.SetSizer(self.data_sizer)

        # ---------------------------------------------

        self.output_panel = wx.Panel(self.data_splitter, size=(175, -1), style=wx.BORDER_STATIC)
        self.output_sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_panel.SetSizer(self.output_sizer)

        output_statictext = wx.StaticText(self.output_panel, label=APP_TEXT_LABELS['SINGLE_GENERATOR.OUTPUT'])
        self.output_sizer.Add(output_statictext, 0, wx.ALL, 5)

        self.output_textctrl = wx.TextCtrl(self.output_panel, style=wx.TE_MULTILINE)
        self.output_textctrl.Bind(wx.EVT_TEXT, self.on_output_changed)
        self.output_sizer.Add(self.output_textctrl, 1, wx.LEFT | wx.RIGHT | wx.EXPAND | wx.BOTTOM, 10)

        # ---------------------------------------------

        self.data_splitter.SplitVertically(self.data_panel, self.output_panel)
        self.data_splitter.SetMinimumPaneSize(175)
        self.field_sizer.Add(self.data_splitter, 2, wx.EXPAND)
        # ------------------------------

        div_footer_panel = wx.Panel(self.field_panel, style=wx.BORDER_STATIC)
        div_footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        div_footer_panel.SetSizer(div_footer_sizer)

        # ---------------------------------------------

        self.rowcount_panel = wx.Panel(div_footer_panel)
        self.rowcount_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.rowcount_panel.SetSizer(self.rowcount_sizer)

        items_count_statictext = wx.StaticText(self.rowcount_panel, label=APP_TEXT_LABELS['SINGLE_GENERATOR.ITER_COUNT'])
        self.rowcount_sizer.Add(items_count_statictext, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.items_count_textctrl = wx.TextCtrl(self.rowcount_panel)
        self.items_count_textctrl.SetValue('1')
        self.rowcount_sizer.Add(self.items_count_textctrl, 1, wx.EXPAND | wx.RIGHT, 20)

        div_footer_sizer.Add(self.rowcount_panel, 1, wx.ALL | wx.EXPAND, 5)
        # ---------------------------------------------

        self.buttons_panel = wx.Panel(div_footer_panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.cancel_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.CANCEL'], size=(75, -1))
        self.cancel_button.Bind(wx.EVT_BUTTON, lambda x: self.Destroy())
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        self.wrap_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.WRAP'], size=(75, -1))
        self.wrap_button.Bind(wx.EVT_BUTTON, self.open_wrapper_frame)
        self.wrap_button.Disable()
        self.buttons_sizer.Add(self.wrap_button, 0, wx.ALL, 5)

        self.generate_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.GENERATE'], size=(75, -1))
        self.generate_button.Bind(wx.EVT_BUTTON, self.start_generate)
        self.buttons_sizer.Add(self.generate_button, 0, wx.ALL, 5)

        div_footer_sizer.Add(self.buttons_panel, 0)
        # ---------------------------------------------

        self.field_sizer.Add(div_footer_panel, 0, wx.EXPAND)
        # ------------------------------

        self.splitter.SplitVertically(self.items_treectrl, self.field_panel, 175)

        header_label = self.load_frame(open_code)
        self.header_statictext.SetLabel(header_label)
        # ---------------


class WrappingFrame(wx.Dialog):

    data_items = list
    query = str

    def wrap(self):
        self.query = f"""INSERT INTO "table_name"("column_name")\nVALUES ("""
        for item in self.data_items:
            if isinstance(item, str):
                self.query += f"'{item}'\n       ,"
            else:
                self.query += f"{item}\n       ,"
        self.query = self.query.rstrip('\n       ,')
        self.query += ');'

    def copy(self, event):
        self.query = self.stc_redactor.GetValue()
        dataobj = wx.TextDataObject()
        dataobj.SetText(self.query)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(dataobj)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
            self.Destroy()
        else:
            wx.MessageBox('Unable to open the clipboard!', 'Error', wx.ICON_ERROR)

    def __init__(self, parent: wx.Frame, data_items: list):
        super().__init__(parent, title=APP_TEXT_LABELS['BUTTON.WRAP'], size=(600, 400),
                         style=wx.CAPTION | wx.CLOSE_BOX)
        self.SetMinSize((400, 300))
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))

        self.data_items = data_items
        self.wrap()

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        self.stc_redactor = wx.stc.StyledTextCtrl(self.panel)
        self.stc_redactor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT,
                                       wx.Font(pointSize=int(APP_PARAMETERS['STC_FONT_SIZE']),
                                               family=wx.FONTFAMILY_TELETYPE,
                                               style=wx.FONTSTYLE_NORMAL,
                                               weight=int(APP_PARAMETERS['STC_FONT_BOLD'])))
        self.stc_redactor.StyleClearAll()
        # Подсветка синтаксиса
        self.stc_redactor.SetLexer(wx.stc.STC_LEX_SQL)
        self.stc_redactor.SetKeyWords(0,
                                      APP_PARAMETERS['SQL_KEYWORDS'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENT, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENTLINE, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENTDOC, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_NUMBER, APP_PARAMETERS['STC_COLOUR_NUMBER'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_CHARACTER, APP_PARAMETERS['STC_COLOUR_STRING'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_STRING, APP_PARAMETERS['STC_COLOUR_OBJECT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_WORD, APP_PARAMETERS['STC_COLOUR_WORD'])
        # Боковое поле
        self.stc_redactor.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.stc_redactor.SetMarginWidth(1, 45)
        self.stc_redactor.SetValue(self.query)
        self.sizer.Add(self.stc_redactor, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)

        # ----------

        self.buttons_panel = wx.Panel(self.panel)
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_panel.SetSizer(self.buttons_sizer)

        self.cancel_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.CANCEL'], size=(75, -1))
        self.cancel_button.Bind(wx.EVT_BUTTON, lambda x: self.Destroy())
        self.buttons_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        self.copy_button = wx.Button(self.buttons_panel, label=APP_TEXT_LABELS['BUTTON.COPY'], size=(75, -1))
        self.copy_button.Bind(wx.EVT_BUTTON, self.copy)
        self.buttons_sizer.Add(self.copy_button, 0, wx.ALL, 5)

        self.sizer.Add(self.buttons_panel, 0, wx.ALIGN_RIGHT)

        self.Layout()
        # ----------
