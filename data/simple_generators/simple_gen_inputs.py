import wx
import os
import sqlite3
import random
from app_parameters import APPLICATION_PATH, APP_TEXT_LABELS


#################################
### Entries
#################################

class BaseSimpleGenInput(wx.Panel):

    sizer: wx.BoxSizer

    @property
    def value(self) -> str: return self.__value

    @value.setter
    def value(self, value) -> str: self.__value = value

    def get_value(self) -> str: return self.value

    
    def __init__(self, parent: wx.Window, sizer_mode: wx.VERTICAL|wx.HORIZONTAL = wx.VERTICAL):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(sizer_mode)
        self.SetSizer(self.sizer)
        
        self.value = ''


class LabeledTextCtrl(BaseSimpleGenInput):

    label: str

    def __init__(self, parent: wx.Window, label: str):
        super().__init__(parent)
        self.label = label

        label_statictext = wx.StaticText(self, label=self.label)
        self.sizer.Add(label_statictext, 0, wx.BOTTOM, 5)

        self.input_textctrl = wx.TextCtrl(self)
        self.input_textctrl.Bind(wx.EVT_TEXT, self.change_value)
        self.sizer.Add(self.input_textctrl, 0, wx.EXPAND)

        self.Layout()

    def change_value(self, event): self.value = self.input_textctrl.GetValue()


class LabeledComboBox(BaseSimpleGenInput):

    label: str
    choosed_items: list
    labeled_items: list

    def __init__(self, parent: wx.Window, label: str, choosed_items: list, labeled_items: list = None):
        super().__init__(parent)
        self.label = label
        self.choosed_items = choosed_items
        if labeled_items is None or len(labeled_items) == 0: self.labeled_items = labeled_items
        else:                                                self.labeled_items = choosed_items

        label_statictext = wx.StaticText(self, label=self.label)
        self.sizer.Add(label_statictext, 0, wx.BOTTOM, 5)

        self.input_combobox = wx.ComboBox(self, choices=self.labeled_items)
        self.input_combobox.Bind(wx.EVT_COMBOBOX, self.change_value)
        self.sizer.Add(self.input_combobox, 0, wx.EXPAND)

        self.Layout()

    def change_value(self, event):
        choosed_item = self.input_combobox.GetValue()
        index = self.labeled_items.index(choosed_item)
        self.value = self.choosed_items[index]


class SelectFromDB(wx.Panel):

    row_count = int

    db_name = str
    column_info = str
    column_name = str

    db_data = list

    def __init__(self, parent: wx.Panel, db_name: str, column_info: str):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.db_name = db_name
        self.column_info = column_info

        with sqlite3.connect(os.path.join(APPLICATION_PATH, 'data/', db_name)) as conn:
            curs = conn.cursor()
            self.col_name = curs.execute(f"""SELECT column_code FROM t_cases_info 
                                                    WHERE table_name = '{self.column_info.split(':')[0]}'
                                                    AND   column_name = '{self.column_info.split(':')[1]}';""").fetchone()[0]

            data = curs.execute(f"""SELECT \"{self.column_info.split(':')[1]}\"
                                            FROM \"{self.column_info.split(':')[0]}\";""").fetchall()
            self.db_data = [item[0] for item in data]

            self.row_count = curs.execute(f"""SELECT COUNT(\"{self.column_info.split(':')[1]}\")
                                                    FROM \"{self.column_info.split(':')[0]}\";""").fetchone()[0]
            curs.close()

        header_statictext = wx.StaticText(self,
                                            label=APP_TEXT_LABELS['SINGLE_GENERATOR.SELECT_DB.SELECT_COUNT'] + str(
                                                self.row_count))
        self.sizer.Add(header_statictext, 0, wx.ALL, 5)

        self.select_listctrl = wx.ListBox(self, choices=self.db_data)
        self.sizer.Add(self.select_listctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.Layout()

    def get_column_name(self) -> str: return self.col_name

    def get_value(self) -> str:
        rnd_item = random.randint(0, self.row_count)
        return self.db_data[rnd_item]