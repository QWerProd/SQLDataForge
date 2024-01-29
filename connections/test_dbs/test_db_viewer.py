import wx

from app.app_parameters import APP_TEXT_LABELS


class TestDBViewer(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title=APP_TEXT_LABELS['TEST_DB_VIEWER.TITLE'], size=(500, 550),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.FRAME_NO_TASKBAR)
        self.SetMinSize((500, 550))
        self.SetMaxSize((500, 550))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.SetIcon(wx.Icon('img/main_icon.png', wx.BITMAP_TYPE_PNG))

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        self.Layout()
