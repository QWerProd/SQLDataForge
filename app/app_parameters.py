from data_controller import DataController as DC

APP_PARAMETERS = {
    'IS_CATCH_CLOSING_APP': str,
    'STC_COLOUR_WORD': str,
    'STC_COLOUR_COMMENT': str,
    'STC_COLOUR_NUMBER': str,
    'STC_COLOUR_STRING': str,
    'STC_FONT_SIZE': str,
    'STC_FONT_BOLD': str
}

for param in APP_PARAMETERS.keys():
    APP_PARAMETERS[param] = DC.ParamChanger(param)
