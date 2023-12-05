import wx
import re
import wx.stc
from app.app_parameters import APP_PARAMETERS


class SimpleEntry(wx.Panel):

    def __init__(self, parent: wx.Panel, title: str, choices: list = None, sizer_mode: int = wx.VERTICAL):
        super().__init__(parent)
        self.title = title
        self.choices = choices
        self.param = None
        self.sizer = wx.BoxSizer(sizer_mode)
        self.SetSizer(self.sizer)

    @property
    def param(self) -> str: return self.__param

    @param.setter
    def param(self, param): self.__param = param


class RadioSelect(SimpleEntry):

    radiobuttons = {}

    def __init__(self, parent: wx.Panel, title: str, choices: list):
        super().__init__(parent, title, choices)

        title_statictext = wx.StaticText(self, label=self.title)
        self.sizer.Add(title_statictext, 0, wx.LEFT | wx.BOTTOM, 5)

        self.start_radiobutton = wx.RadioButton(self, id=0, label=self.choices[0], style=wx.RB_GROUP)
        self.start_radiobutton.Bind(wx.EVT_RADIOBUTTON, self.change_param)
        self.sizer.Add(self.start_radiobutton, 0, wx.LEFT | wx.BOTTOM, 2)
        self.radiobuttons[0] = self.start_radiobutton

        for i in range(1, len(self.choices)):
            radiobutton = wx.RadioButton(self, id=i, label=self.choices[i])
            radiobutton.Bind(wx.EVT_RADIOBUTTON, self.change_param)
            self.sizer.Add(radiobutton, 0, wx.LEFT | wx.BOTTOM, 2)
            self.radiobuttons[i] = radiobutton

        self.Layout()

    def change_param(self, event):
        rb = event.GetEventObject()
        self.param = rb.GetLabel()

    def set_value(self, value):
        """Принимает имя переключателя"""
        rb = self.radiobuttons[value]
        rb.SetValue(True)
        self.param = value


class CheckboxPoint(SimpleEntry):
    def __init__(self, parent: wx.Panel, title: str):
        super().__init__(parent, title)

        self.checkbox = wx.CheckBox(self, label=self.title)
        self.checkbox.Bind(wx.EVT_CHECKBOX, self.change_param)
        self.sizer.Add(self.checkbox, 0, wx.ALL, 5)

        self.Layout()

    def change_param(self, event):
        value = self.checkbox.GetValue()
        self.param = value if value else False

    def set_value(self, value):
        """Принимает булевое значение в виде строки"""
        self.checkbox.SetValue(value == 'True')
        self.param = (value == 'True')


class SelectorBox(SimpleEntry):
    def __init__(self, parent: wx.Panel, title: str, choices: list):
        super().__init__(parent, title, choices=list(map(lambda x: x.split('&'), choices)), sizer_mode=wx.HORIZONTAL)
        label_choices = [item[1] for item in self.choices]

        statictext = wx.StaticText(self, label=self.title)
        self.sizer.Add(statictext, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.choicesbox = wx.Choice(self, choices=label_choices, size=(100, -1))
        self.choicesbox.Bind(wx.EVT_CHOICE, self.change_param)
        self.sizer.Add(self.choicesbox, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

        self.Layout()

    def change_param(self, event): self.param = self.choices[self.choicesbox.GetSelection()][0]

    def set_value(self, value):
        """Принимает имя поля"""
        for i in range(len(self.choices)):
            if value == self.choices[i][0]:
                self.choicesbox.SetSelection(i)
                self.param = self.choices[i][0]


class HEXEnter(SimpleEntry):
    def __init__(self, parent: wx.Panel, title: str):
        super().__init__(parent, title, sizer_mode=wx.HORIZONTAL)

        statictext = wx.StaticText(self, label=self.title, size=(-1, -1))
        self.sizer.Add(statictext, 1, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.hex_textctrl = wx.TextCtrl(self, size=(85, -1))
        self.hex_textctrl.Bind(wx.EVT_TEXT, self.change_param)
        self.sizer.Add(self.hex_textctrl, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.colour_panel = wx.Panel(self, size=(10, 24), style=wx.BORDER_STATIC)
        self.sizer.Add(self.colour_panel, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

        self.Layout()

    def change_param(self, event):
        pattern = re.compile("(?i)#(?:[0-9a-f]{6}|[0-9a-f]{3})(?=[;,)])")
        value = self.hex_textctrl.GetValue() + ';'
        result = pattern.match(value)
        if result is not None:
            self.colour_panel.SetBackgroundColour(result.group(0))
            self.param = str(result.group(0))
            self.colour_panel.Refresh()

    def set_value(self, value):
        self.hex_textctrl.SetValue(value)
        self.colour_panel.SetBackgroundColour(value)
        self.param = value
        self.colour_panel.Refresh()


class HeaderGroup(wx.Panel):
    def __init__(self, parent: wx.Panel, title: str):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        header = wx.StaticText(self, label=title)
        header.SetFont(font)
        self.sizer.Add(header, 0, wx.LEFT | wx.TOP | wx.EXPAND, 15)

        staticline = wx.StaticLine(self)
        self.sizer.Add(staticline, 0, wx.LEFT | wx.BOTTOM | wx.EXPAND, 5)

        self.Layout()

    def set_value(self, value):
        pass


class SpinNumber(SimpleEntry):
    def __init__(self, parent: wx.Panel, title: str, choices: list):
        super().__init__(parent, title, choices, sizer_mode=wx.HORIZONTAL)

        statictext = wx.StaticText(self, label=title)
        self.sizer.Add(statictext, 1, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.spinctrl = wx.SpinCtrl(self, min=int(self.choices[0]), max=int(self.choices[1]), size=(100, -1))
        self.spinctrl.Bind(wx.EVT_SPINCTRL, self.change_param)
        self.sizer.Add(self.spinctrl, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

    def change_param(self, event):
        value = self.spinctrl.GetValue()
        self.param = int(value)

    def set_value(self, value):
        self.spinctrl.SetValue(str(value))
        self.param = int(value)


class CodeRedactor(SimpleEntry):
    def __init__(self, parent: wx.Panel, title: str = None):
        super().__init__(parent, title, sizer_mode=wx.HORIZONTAL)

        self.styledtextctrl = wx.stc.StyledTextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 150))
        self.styledtextctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT,
                                       wx.Font(pointSize=int(APP_PARAMETERS['STC_FONT_SIZE']),
                                               family=wx.FONTFAMILY_TELETYPE,
                                               style=wx.FONTSTYLE_NORMAL,
                                               weight=int(APP_PARAMETERS['STC_FONT_BOLD'])))
        self.styledtextctrl.StyleClearAll()
        # Подсветка синтаксиса
        sql_keywords = ("insert into values create table as text number primary key integer not null where and or like"
                        " if exists index on is update set")
        self.styledtextctrl.SetLexer(wx.stc.STC_LEX_SQL)
        self.styledtextctrl.SetKeyWords(0, sql_keywords)
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_COMMENT, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_COMMENTLINE, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_COMMENTDOC, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_NUMBER, APP_PARAMETERS['STC_COLOUR_NUMBER'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_CHARACTER, APP_PARAMETERS['STC_COLOUR_STRING'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_STRING, APP_PARAMETERS['STC_COLOUR_STRING'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_WORD, APP_PARAMETERS['STC_COLOUR_WORD'])
        # Боковое поле
        self.styledtextctrl.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.styledtextctrl.SetMarginWidth(1, 45)
        self.styledtextctrl.SetValue("""UPDATE t_persons as p\nSET    p.age = 18\nWHERE  p.first_name = 'Smith'; -- Only one Smith on this table :)""")
        self.sizer.Add(self.styledtextctrl, 1, wx.EXPAND)

    def change_param(self, param): pass

    def set_value(self, value): pass
