from data_controller import DataController as DC

APP_PARAMETERS = {
    'IS_CATCH_CLOSING_APP': str,
    'STC_COLOUR_WORD': str,
    'STC_COLOUR_COMMENT': str,
    'STC_COLOUR_NUMBER': str,
    'STC_COLOUR_STRING': str,
    'STC_FONT_SIZE': str,
    'STC_FONT_BOLD': str,
    'KEY_EXECUTE': str,
    'KEY_CLEAR_ALL': str,
    'KEY_REFRESH': str,
    'KEY_NEW_INSTANCE': str,
    'KEY_SAVE_SQL': str,
    'KEY_SETTINGS': str,
    'KEY_CREATE_UDB_WIZARD': str,
    'KEY_UDB_VIEWER': str,
    'FORMAT_DATE': str
}

for param in APP_PARAMETERS.keys():
    APP_PARAMETERS[param] = DC.ParamChanger(param)
