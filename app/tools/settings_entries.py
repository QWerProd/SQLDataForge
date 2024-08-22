import wx
import re
import os
from wx.core import VERTICAL
import wx.stc
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, TextEditMixin
from app_parameters import APP_PARAMETERS, APP_TEXT_LABELS


class SimpleEntry(wx.Panel):

    def __init__(self, parent: wx.Panel, title: str, choices: list = None, sizer_mode: int = wx.VERTICAL, size: list = None):
        pan_size = size if size is not None else (-1, 28)
        super().__init__(parent, size=pan_size)
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
        self.start_radiobutton.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.start_radiobutton.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.sizer.Add(self.start_radiobutton, 0, wx.LEFT | wx.BOTTOM, 2)
        self.radiobuttons[0] = self.start_radiobutton

        for i in range(1, len(self.choices)):
            radiobutton = wx.RadioButton(self, id=i, label=self.choices[i])
            radiobutton.Bind(wx.EVT_RADIOBUTTON, self.change_param)
            radiobutton.Bind(wx.EVT_ENTER_WINDOW, lambda x: radiobutton.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
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
        super().__init__(parent, title, sizer_mode=wx.HORIZONTAL)

        statictext = wx.StaticText(self, label=self.title)
        self.sizer.Add(statictext, 1, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.checkbox = wx.CheckBox(self, style=wx.ALIGN_RIGHT)
        self.checkbox.Bind(wx.EVT_CHECKBOX, self.change_param)
        self.checkbox.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.checkbox.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.sizer.Add(self.checkbox, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

        self.Layout()

    def change_param(self, event):
        value = self.checkbox.GetValue()
        self.param = value if value else False

    def set_value(self, value):
        """Принимает булевое значение в виде строки"""
        self.checkbox.SetValue(value == 'True')
        self.param = (value == 'True')


class SelectorBox(SimpleEntry):

    label_choices = list

    def __init__(self, parent: wx.Panel, title: str, choices: list, label_choices: list = None):
        super().__init__(parent, title, choices=choices, sizer_mode=wx.HORIZONTAL)
        if label_choices is None:
            self.label_choices = choices
        else:
            self.label_choices = label_choices

        statictext = wx.StaticText(self, label=self.title)
        self.sizer.Add(statictext, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.choicesbox = wx.Choice(self, choices=self.label_choices, size=(125, -1))
        self.choicesbox.Bind(wx.EVT_CHOICE, self.change_param)
        self.choicesbox.Bind(wx.EVT_ENTER_WINDOW, lambda x: self.choicesbox.SetCursor(wx.Cursor(wx.CURSOR_HAND)))
        self.sizer.Add(self.choicesbox, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

        self.Layout()

    def change_param(self, event): self.param = self.choices[self.choicesbox.GetSelection()]

    def set_value(self, value):
        """Принимает имя поля"""
        for i in range(len(self.choices)):
            if value == self.choices[i]:
                self.choicesbox.SetSelection(i)
                self.param = self.choices[i]


class HEXEnter(SimpleEntry):
    def __init__(self, parent: wx.Panel, title: str):
        super().__init__(parent, title, sizer_mode=wx.HORIZONTAL)

        statictext = wx.StaticText(self, label=self.title, size=(-1, -1))
        self.sizer.Add(statictext, 1, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.hex_textctrl = wx.TextCtrl(self, size=(110, -1))
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
        self.hex_textctrl.SetValue(str(value))
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

        self.spinctrl = wx.SpinCtrl(self, min=int(self.choices[0]), max=int(self.choices[1]), size=(125, -1))
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

        self.styledtextctrl = wx.stc.StyledTextCtrl(self, style=wx.TE_MULTILINE)
        self.styledtextctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT,
                                         wx.Font(pointSize=int(APP_PARAMETERS['STC_FONT_SIZE']),
                                                 family=wx.FONTFAMILY_TELETYPE,
                                                 style=wx.FONTSTYLE_NORMAL,
                                                 weight=int(APP_PARAMETERS['STC_FONT_BOLD'])))
        self.styledtextctrl.StyleClearAll()
        self.styledtextctrl.SetLexer(wx.stc.STC_LEX_SQL)
        self.styledtextctrl.SetKeyWords(0, APP_PARAMETERS['SQL_KEYWORDS'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_COMMENT, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_COMMENTLINE, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_COMMENTDOC, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_NUMBER, APP_PARAMETERS['STC_COLOUR_NUMBER'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_CHARACTER, APP_PARAMETERS['STC_COLOUR_STRING'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_STRING, APP_PARAMETERS['STC_COLOUR_OBJECT'])
        self.styledtextctrl.StyleSetForeground(wx.stc.STC_SQL_WORD, APP_PARAMETERS['STC_COLOUR_WORD'])
        # Боковое поле
        self.styledtextctrl.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.styledtextctrl.SetMarginWidth(1, 45)
        for textrow in self.title.split('\\n'):
            self.styledtextctrl.AppendText(textrow + '\n')
        self.sizer.Add(self.styledtextctrl, 1, wx.EXPAND)

    def change_param(self, param): pass

    def set_value(self, value): pass


class TableSystemColumns(wx.ListCtrl, ListCtrlAutoWidthMixin, TextEditMixin):

    parent = wx.Panel
    title = list
    choices = list
    params = dict

    def __init__(self, parent: wx.Panel, title: list, choices: list):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        ListCtrlAutoWidthMixin.__init__(self)
        TextEditMixin.__init__(self)
        self.parent = parent
        self.title = title
        self.choices = choices
        self.params = {}
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.change_param)

    def set_value(self, value):
        size = self.GetSize()
        # Добавление заголовков (без id)
        for colname in self.title:
            self.AppendColumn(colname)
            self.resizeColumn(100)
        self.SetHeaderAttr(wx.ItemAttr(self.GetForegroundColour(),
                                       self.GetBackgroundColour(),
                                       wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)))
        # Добавление значений
        for rowvalue in self.choices:
            self.Append(rowvalue[1:])

    def change_param(self, event):
        row_id = event.GetIndex()
        col_id = event.GetColumn()
        new_value = event.GetText()

        if col_id == 0:
            return
        else:
            self.params[self.choices[row_id][0]] = new_value

    def get_params(self) -> dict: return self.params


class MaskedTextEntry(SimpleEntry):

    mask = str

    def __init__(self, parent: wx.Panel, title: str, mask: str = None):
        super().__init__(parent, title, sizer_mode=wx.HORIZONTAL)
        self.mask = mask

        statictext = wx.StaticText(self, label=self.title)
        self.sizer.Add(statictext, 1, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.textctrl = wx.TextCtrl(self, size=(125, -1))
        self.textctrl.Bind(wx.EVT_TEXT, self.change_param)
        self.sizer.Add(self.textctrl, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

        self.Layout()

    def change_param(self, event):
        if self.mask is not None:
            try:
                masked = '{:' + self.mask + '}'
                date = masked.format(self.param)
                self.param = self.textctrl.GetValue()
            except:
                return
        else:
            self.param = self.textctrl.GetValue()

    def set_value(self, value):
        self.textctrl.SetValue(str(value))
        self.param = value


class PathFileTextEntry(SimpleEntry):

    path_to_file = bool
    wildcard = str

    def __init__(self, parent: wx.Panel, title: str, wildcard: str = None, path_to_file: bool = False):
        super().__init__(parent, title, sizer_mode=wx.HORIZONTAL)
        self.path_to_file = path_to_file
        self.wildcard = wildcard

        statictext = wx.StaticText(self, label=title)
        self.sizer.Add(statictext, 1, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.textctrl = wx.TextCtrl(self, size=(250, 22))
        self.textctrl.Bind(wx.EVT_TEXT, self.change_param)
        self.sizer.Add(self.textctrl, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.button = wx.Button(self, label='...', size=(25, 24))
        if self.path_to_file:
            self.button.Bind(wx.EVT_BUTTON, self.explore_file)
        else:
            self.button.Bind(wx.EVT_BUTTON, self.explore_path)
        self.sizer.Add(self.button, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 15)

        self.Layout()

    def change_param(self, event):
        self.param = self.textctrl.GetValue()

    def set_value(self, value):
        self.textctrl.SetValue(str(value))
        self.param = value

    def explore_path(self, event):
        with wx.DirDialog(self, APP_TEXT_LABELS['NEW_UDB_WIZARD.FIRST_PAGE.DIR_DIALOG'],
                          style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            
            self.param = dialog.GetPath()
            self.textctrl.SetValue(self.param)
    
    def explore_file(self, event):
        with wx.FileDialog(self, APP_TEXT_LABELS['FILE_DIALOG.CAPTION_CHOOSE'],
                           wildcard=self.wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            
            self.param = os.path.join(dialog.GetPath(), dialog.GetFilename())
            self.textctrl.SetValue(self.param)

