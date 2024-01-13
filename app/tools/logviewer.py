import wx
import sqlite3
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin
from wx.stc import StyledTextCtrl
from app.app_parameters import APP_TEXT_LABELS, APP_PARAMETERS
from app.error_catcher import ErrorCatcher


class Logviewer(wx.Frame):
    catcher = ErrorCatcher

    def get_errorlog(self) -> list:
        with sqlite3.connect('app/app.db') as app_conn:
            cursor = app_conn.cursor()
            try:
                log_data = cursor.execute(f"""SELECT el.error_code, lt.text, el.date_catched 
                                              FROM t_error_log el
                                              JOIN t_lang_text lt ON el.error_code||'.CAPTION' = lt.label
                                              WHERE lt.lang = '{APP_PARAMETERS['APP_LANGUAGE']}'
                                              ORDER BY el.id DESC;""").fetchall()
            except sqlite3.Error as e:
                self.catcher.error_message('E014', 'sqlite_errorname: ' + e.sqlite_errorname)
            finally:
                cursor.close()
        return log_data

    def get_execution_log(self) -> str:
        with sqlite3.connect('app/app.db') as app_conn:
            cursor = app_conn.cursor()
            try:
                log_data = cursor.execute(f"""SELECT el.query_text, el.date_execute
                                              FROM t_execution_log el
                                              ORDER BY el.id DESC;""").fetchall()
            except sqlite3.Error as e:
                self.catcher.error_message('E014', 'sqlite_errorname: ' + e.sqlite_errorname)
            finally:
                cursor.close()

        log_text = ''
        for log_row in log_data:
            log_text += f'/*----------Query executed on {log_row[1]}----------*/\n' + log_row[0] + '\n\n'

        return log_text

    def __init__(self, catcher: ErrorCatcher):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['MAIN.MAIN_MENU.TOOLS.LOGVIEWER'], size=(600, 450),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.SetMinSize((600, 450))
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))
        self.catcher = catcher

        self.notebook = wx.Notebook(self, style=wx.NB_BOTTOM)

        # ----------

        self.errorlog_panel = wx.Panel(self.notebook)
        self.errorlog_sizer = wx.BoxSizer(wx.VERTICAL)
        self.errorlog_panel.SetSizer(self.errorlog_sizer)

        self.errorlog_report = ReportViewer(self.errorlog_panel,
                                            (APP_TEXT_LABELS['LOGVIEWER.ERROR_LOG.HEADER.ERROR_CODE'],
                                             APP_TEXT_LABELS['LOGVIEWER.ERROR_LOG.HEADER.ERROR_CAPTION'],
                                             APP_TEXT_LABELS['LOGVIEWER.ERROR_LOG.HEADER.ERROR_CATCHED']),
                                            self.get_errorlog())
        self.errorlog_sizer.Add(self.errorlog_report, 1, wx.EXPAND)

        self.notebook.AddPage(self.errorlog_panel, APP_TEXT_LABELS['LOGVIEWER.ERROR_LOG'])
        # ----------

        self.executionlog_panel = wx.Panel(self.notebook)
        self.executionlog_sizer = wx.BoxSizer(wx.VERTICAL)
        self.executionlog_panel.SetSizer(self.executionlog_sizer)

        self.stc_redactor = StyledTextCtrl(self.executionlog_panel)
        # Настройки шрифта
        self.stc_redactor.StyleSetFont(wx.stc.STC_STYLE_DEFAULT,
                                       wx.Font(pointSize=int(APP_PARAMETERS['STC_FONT_SIZE']),
                                               family=wx.FONTFAMILY_TELETYPE,
                                               style=wx.FONTSTYLE_NORMAL,
                                               weight=int(APP_PARAMETERS['STC_FONT_BOLD'])))
        self.stc_redactor.StyleClearAll()
        # Подсветка синтаксиса
        self.stc_redactor.SetLexer(wx.stc.STC_LEX_SQL)
        self.stc_redactor.SetKeyWords(0, APP_PARAMETERS['SQL_KEYWORDS'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENT, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENTLINE, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_COMMENTDOC, APP_PARAMETERS['STC_COLOUR_COMMENT'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_NUMBER, APP_PARAMETERS['STC_COLOUR_NUMBER'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_CHARACTER, APP_PARAMETERS['STC_COLOUR_STRING'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_STRING, APP_PARAMETERS['STC_COLOUR_STRING'])
        self.stc_redactor.StyleSetForeground(wx.stc.STC_SQL_WORD, APP_PARAMETERS['STC_COLOUR_WORD'])
        # Боковое поле
        self.stc_redactor.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.stc_redactor.SetMarginWidth(1, 45)

        self.stc_redactor.SetValue(self.get_execution_log())
        self.executionlog_sizer.Add(self.stc_redactor, 1, wx.EXPAND)

        self.notebook.AddPage(self.executionlog_panel, APP_TEXT_LABELS['LOGVIEWER.EXECUTION_LOG'])
        # ----------


class ReportViewer(wx.ListCtrl, ListCtrlAutoWidthMixin, ColumnSorterMixin):
    columns = list
    choices = dict

    def __init__(self, parent: wx.Window, columns: list, choices: list):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        ListCtrlAutoWidthMixin.__init__(self)
        ColumnSorterMixin.__init__(self, len(columns))
        self.columns = columns
        self.choices = {}
        # Setting the dict for list
        for i in range(len(choices)):
            self.choices[i + 1] = choices[i]

        # Appending headers
        for column in columns:
            self.AppendColumn(column)
            self.resizeColumn(150)
            self.SetHeaderAttr(wx.ItemAttr(self.GetForegroundColour(),
                                           self.GetBackgroundColour(),
                                           wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)))

        # Appending data
        self.itemDataMap = self.choices
        for key, value in self.choices.items():
            index = self.Append(value)
            self.SetItemData(index, key)

    def GetListCtrl(self):
        return self
