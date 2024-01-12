CREATE TABLE IF NOT EXISTS "t_databases" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"dbname"	TEXT NOT NULL,
	"path"	TEXT NOT NULL,
	"field_name"	TEXT,
	"description"	TEXT,
	"is_valid"	TEXT NOT NULL DEFAULT 'Y');
/
CREATE TABLE IF NOT EXISTS "t_params" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"param_name"	TEXT NOT NULL UNIQUE,
	"param_value"	TEXT,
	"param_type"	TEXT NOT NULL DEFAULT 'SYSTEM',
	"param_label"	TEXT DEFAULT NULL,
	"update_layout"	INTEGER DEFAULT 0);
/
CREATE TABLE IF NOT EXISTS "t_err_codes" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"err_code"	TEXT NOT NULL,
	"title"	    TEXT NOT NULL,
	"message"	TEXT NOT NULL DEFAULT NULL);
/
CREATE TABLE IF NOT EXISTS "t_lang_text" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"label"	TEXT NOT NULL,
	"lang"	TEXT NOT NULL,
	"text"	TEXT NOT NULL);
/
CREATE TABLE IF NOT EXISTS "t_settings_items" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"id_fk"	INTEGER,
	"sett_label"	TEXT NOT NULL,
	"is_valid"	TEXT NOT NULL DEFAULT 'Y');
/
CREATE TABLE IF NOT EXISTS "t_settings_items_params" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"id_param"	INTEGER,
	"id_parent"	INTEGER NOT NULL,
	"posid"	INTEGER NOT NULL,
	"entry_type"	TEXT NOT NULL,
	"entry_label"	TEXT,
	"entry_choices"	TEXT DEFAULT NULL,
	"entry_label_choices"	TEXT,
	"is_valid"	TEXT NOT NULL DEFAULT 'Y');
/
CREATE TABLE IF NOT EXISTS "t_simple_gen" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"gen_code"	TEXT NOT NULL,
	"gen_name"	TEXT,
	"gen_type"	TEXT NOT NULL,
	"generator"	TEXT DEFAULT NULL,
	"is_valid"	TEXT NOT NULL DEFAULT 'Y');
/
CREATE TABLE IF NOT EXISTS "t_simple_gen_entries" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"id_field"	INTEGER NOT NULL,
	"posid"	INTEGER NOT NULL,
	"entry_name"	TEXT NOT NULL,
	"entry_type"	TEXT NOT NULL);
/
CREATE TABLE IF NOT EXISTS "t_error_log" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"error_code"	TEXT NOT NULL,
	"date_catched"	TEXT NOT NULL);
/
CREATE TABLE IF NOT EXISTS "t_execution_log" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"query_text"	TEXT NOT NULL,
	"date_execute"	TEXT NOT NULL);
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('MAIN.MAIN_MENU.FILE.GENERATE','ru','Генерировать'),
	 ('MAIN.MAIN_MENU.FILE.REFRESH','ru','Обновить'),
	 ('MAIN.MAIN_MENU.FILE.CLEAR_ALL','ru','Очистить'),
	 ('BUTTON.SAVE','ru','Сохранить'),
	 ('MAIN.MAIN_MENU.CONNECTIONS.ADD_UDB','ru','Добавить пБД...'),
	 ('MAIN.MAIN_MENU.CONNECTIONS.CREATE_UDB','ru','Создать пБД...'),
	 ('MAIN.MAIN_MENU.CONNECTIONS.UDB_VIEWER','ru','Все доступные пБД...'),
	 ('MAIN.MAIN_MENU.FILE','ru','Файл'),
	 ('MAIN.MAIN_MENU.CONNECTIONS','ru','Подключения'),
	 ('MAIN.MAIN_MENU.GENERATOR','ru','Генератор'),
	 ('MAIN.MAIN_MENU.GENERATOR.SIMPLE_GENERATORS','ru','Простые генераторы'),
	 ('MAIN.MAIN_MENU.TOOLS','ru','Инструменты'),
	 ('MAIN.MAIN_MENU.TOOLS.SETTINGS','ru','Настройки...'),
	 ('MAIN.TOOLBAR.SHORTHELP.GENERATE','ru','Сгенерировать SQL-код'),
	 ('MAIN.TOOLBAR.SHORTHELP.CLEAR_ALL','ru','Очистить поля'),
	 ('MAIN.TOOLBAR.SHORTHELP.REFRESH','ru','Обновить список пБД'),
	 ('MAIN.TOOLBAR.SHORTHELP.SAVE_SQL','ru','Сохранить скрипт'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.TABLE_NAME','ru','Имя таблицы:'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.ROW_COUNT','ru','Кол-во строк:'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_NAME','ru','Имя столбца'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_TYPE','ru','Тип столбца'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE','ru','Главная'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE.CREATE_TABLE','ru','Создать таблицу'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE.ADD_ID','ru','Добавить ID для строк таблицы'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE.INIT_VALUE_ID','ru','Начальное значение ID:'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE','ru','Таблица'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE','ru','Индексы'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.NEW_INDEX','ru','Новый индекс'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.DELETE_INDEX','ru','Удалить'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.INDEX_NAME','ru','Имя индекса:'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.INDEX_COLUMNS','ru','Столбцы:'),
	 ('MAIN.STATUSBAR.STATUS.WAITING','ru','Ожидание...'),
	 ('MAIN.STATUSBAR.STATUS.GENERATING','ru','Генерация запроса...'),
	 ('MAIN.STATUSBAR.STATUS.DONE','ru','Готово'),
	 ('NEW_UDB_WIZARD.CANCEL_MESSAGE.MESSAGE','ru','Все введенные данные будут неизбежно утеряны!'),
	 ('MESSAGE_BOX.CAPTION_APPROVE','ru','Вы уверены?'),
	 ('NEW_UDB_WIZARD.BUTTON.NEXT','ru','Далее ->'),
	 ('BUTTON.CANCEL','ru','Отмена'),
	 ('NEW_UDB_WIZARD.BUTTON.PREVIOUS','ru','<- Назад'),
	 ('NEW_UDB_WIZARD.BUTTON.FINISH','ru','Готово'),
	 ('NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.MESSAGE','ru','Все поля должны быть заполнены!'),
	 ('NEW_UDB_WIZARD.INFORMATION','ru','Данный мастер предназначен для создания рабочего каркаса пБД'),
	 ('NEW_UDB_WIZARD.TITLE','ru','Мастер создания пБД'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.DB_PATH','ru','Путь к файлу'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME','ru','Имя файла'),
	 ('NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.CAPTION','ru','Заполните поля'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.TITLE','ru','Укажите имя создаваемого файла и путь, в котором нужно сохранить файл.'),
	 ('NEW_UDB_WIZARD.SECOND_PAGE.TITLE','ru','Укажите нужно ли добавлять создаваемую пБД в SQLDataForge.
Заполните все поля при необходимости.'),
	 ('NEW_UDB_WIZARD.SECOND_PAGE.ADD_IN_SDFORGE','ru','Добавить в SQLDataForge'),
	 ('NEW_UDB_WIZARD.SECOND_PAGE.DB_ALIAS','ru','Псевдоним');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('NEW_UDB_WIZARD.SECOND_PAGE.DB_DESC','ru','Описание'),
	 ('NEW_UDB_WIZARD.THIRD_PAGE.INFO_TITLE','ru','Информация о файле'),
	 ('NEW_UDB_WIZARD.THIRD_PAGE.INFO_ADDON','ru','Дополнительная информация'),
	 ('NEW_UDB_WIZARD.THIRD_PAGE.INFO_CHECK','ru','Проверьте правильность указанных данных.'),
	 ('NEW_UDB_WIZARD.FINISH.SUCCESS_MESSAGE.CAPTION','ru','Макет пБД создан!'),
	 ('NEW_UDB_WIZARD.FINISH.SUCCESS_MESSAGE.MESSAGE','ru','Макет пользовательской Базы Данных создан в '),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.DIR_DIALOG','ru','Выберите путь...'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.ENTER_CONDITION_HERE','ru','-- Введите условия здесь'),
	 ('MAIN.STATUSBAR.TIMER.GENERATE_TIME','ru','Сгенерировано за: '),
	 ('MAIN.STATUSBAR.TIMER.ALL_TIME','ru',' с., всего: '),
	 ('FILE_DIALOG.CAPTION_SAVE','ru','Сохранить как...'),
	 ('FILE_DIALOG.WILDCARD_DB','ru','Файл БД SQLite (*.db)|*.db'),
	 ('MAIN.MESSAGE_BOX.SAVE_SCRIPT.FILE','ru','Файл '),
	 ('MAIN.MESSAGE_BOX.SAVE_SCRIPT.SAVED','ru',' сохранен в '),
	 ('MAIN.STATUSBAR.STATUS.SAVED','ru','Сохранено'),
	 ('MAIN.MESSAGE_BOX.CLEAR_FORM.MESSAGE','ru','Вы уверены, что хотите очистить все поля?
Несохраненный запрос будет удален навсегда!'),
	 ('MAIN.MESSAGE_BOX.CLEAR_FORM.CAPTION','ru','Подтверждение очистки полей'),
	 ('MAIN.MESSAGE_BOX.CLOSE_APP.MESSAGE','ru','Вы уверены, что хотите выйти из приложения?'),
	 ('MAIN.MESSAGE_BOX.CLOSE_APP.CAPTION','ru','Подтвердите выход'),
	 ('MAIN.MESSAGE_BOX.INIT.MESSAGE1','ru','Добавлено новых пБД: '),
	 ('MAIN.MESSAGE_BOX.INIT.MESSAGE2','ru',', ошибок: '),
	 ('MAIN.MESSAGE_BOX.INIT.CAPTION','ru','Обновление'),
	 ('CONNECTION_VIEWER.DB_DESC.HINT','ru','Описание отсутствует...'),
	 ('CONNECTION_VIEWER.DB_TREE.LOCAL_UDB','ru','локальные пБД'),
	 ('CONNECTION_VIEWER.DB_TREE.GLOBAL_UDB','ru','внешние пБД'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_CONNECTION.MESSAGE','ru','Вы не можете удалить пБД из локального репозитория'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.CAPTION','ru','Ошибка удаления'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_SINGLE_CONNECTION.MESSAGE','ru','Должна остаться хотя бы одна пБД!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_SINGLE_CONNECTION.CAPTION','ru','Ошибка удаления'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.SUCCESS_SAVE_CHANGES.MESSAGE','ru','пБД успешно изменена!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.SUCCESS_SAVE_CHANGES.CAPTION','ru','Успешное изменение'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.ERROR_SAVE_CHANGES.CAPTION','ru','Ошибка сохранения'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.CLOSE_ATTENTION.MESSAGE','ru','Несохраненные данные будут удалены!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.CLOSE_ATTENTION.CAPTION','ru','Вы уверены, что хотите закрыть окно?'),
	 ('CONNECTION_VIEWER.TITLE','ru','Доступные пБД'),
	 ('CONNECTION_VIEWER.DB_INFO','ru','Сведения о пБД'),
	 ('CONNECTION_VIEWER.DB_NAME','ru','Имя:'),
	 ('CONNECTION_VIEWER.DB_ALIAS','ru','Псевдоним:'),
	 ('CONNECTION_VIEWER.DB_PATH','ru','Путь:'),
	 ('CONNECTION_VIEWER.DB_DESC','ru','Описание:'),
	 ('BUTTON.CLOSE','ru','Закрыть'),
	 ('FILE_DIALOG.CAPTION_CHOOSE','ru','Выберите файл...'),
	 ('NEW_CONN.MESSAGE_BOX.CLOSE.MESSAGE','ru','Введенные данные будут удалены!'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_FALSE.CAPTION','ru','Пустой путь'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_FALSE.MESSAGE','ru','Введите корректный путь к пБД!'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.MESSAGE','ru','Тестовое подключение успешно!'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.CAPTION','ru','Успешное подключение'),
	 ('NEW_CONN.MESSAGE_BOX.WITHOUT_TEXT_CONN.MESSAGE','ru','Вы пытаетесь добавить пБД без тестирования подключения!
Для продолжения работы подтвердите добавление!'),
	 ('NEW_CONN.MESSAGE_BOX.WITHOUT_TEXT_CONN.CAPTION','ru','Подтвердите добавление пБД'),
	 ('NEW_CONN.MESSAGE_BOX.ADDING_UDB_TRUE.MESSAGE','ru','пБД успешно добавлена!');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('NEW_CONN.MESSAGE_BOX.ADDING_UDB_TRUE.CAPTION','ru','Успешное добавление'),
	 ('NEW_CONN.TITLE','ru','Новое подключение'),
	 ('NEW_CONN.DB_NAME','ru','Имя пБД:'),
	 ('NEW_CONN.DB_PATH','ru','Путь к пБД:'),
	 ('NEW_CONN.DB_DESC.HINT','ru','Введите описание пБД...'),
	 ('NEW_CONN.DB_DESC','ru','Описание пБД:'),
	 ('BUTTON.TEST','ru','Тест...'),
	 ('BUTTON.APPLY','ru','Применить'),
	 ('BUTTON.GENERATE','ru','Генерация'),
	 ('SINGLE_GENERATOR.ITER_COUNT','ru','Кол-во итераций:'),
	 ('SINGLE_GENERATOR.OUTPUT','ru','Вывод:'),
	 ('SINGLE_GENERATOR.TITLE','ru','Генератор простых значений'),
	 ('SINGLE_GENERATOR.MESSAGE_BOX.ERROR_GENERATE.CAPTION','ru','Ошибка значения'),
	 ('SINGLE_GENERATOR.MESSAGE_BOX.ERROR_GENERATE.MESSAGE','ru','Вводимые значения должны быть целыми числами!
Первое значение не должно быть больше или равно второму значению!'),
	 ('SINGLE_GENERATOR.GO_GENERATE','ru','Сгенерируйте поле'),
	 ('SINGLE_GENERATOR.SELECT_DB.SELECT_COUNT','ru','Количество строк выборки: '),
	 ('APP.SIMPLE_GEN.RAND_NUMBER.MINVALUE','ru','Минимальное число:'),
	 ('APP.SIMPLE_GEN.RAND_NUMBER.MAXVALUE','ru','Максимальное число:'),
	 ('APP.SIMPLE_GEN.RAND_NUMBER','ru','Случ. число'),
	 ('APP.SIMPLE_GEN.RAND_DATE','ru','Случ. дата'),
	 ('APP.SETTINGS.THEME','ru','Оформление'),
	 ('APP.SETTINGS.THEME.GENERAL','ru',''),
	 ('APP.SETTINGS.THEME.REDACTOR','ru','Редактор SQL'),
	 ('APP.SETTINGS.SYSTEM','ru','Системные'),
	 ('APP.SETTINGS.SYSTEM.GENERAL','ru','Общее'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS','ru','Горячие клавиши'),
	 ('APP.SETTINGS.SYSTEM.PARAMETERS','ru','Параметры'),
	 ('APP.SETTINGS.SYSTEM.REDACTOR.FONT_COLOR','ru','Цвет шрифта'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.IS_CATCH_CLOSING_APP','ru','Требовать подтверждение для выхода'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_WORD','ru','Цвет ключевых слов:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_COMMENT','ru','Цвет комментариев:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_NUMBER','ru','Цвет чисел:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_FONT_SIZE','ru','Размер шрифта:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_STRING','ru','Цвет строк:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_FONT_BOLD','ru','Начертание шрифта:'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.FORMAT_DATE','ru','Формат столбцов даты:'),
	 ('APP.SETTINGS.SYSTEM.REDACTOR.FONT_SETTINGS','ru','Параметры шрифта'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.TABLE_TITLE','ru','Описание:Сочетание клавиш'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.APP_SETTINGS','ru','Настройки приложения'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.APP_LANGUAGE','ru','Язык приложения:'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_EXECUTE','ru','Генерировать запрос'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_CLEAR_ALL','ru','Очистить поля'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_REFRESH','ru','Обновить дерево БД'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_NEW_INSTANCE','ru','Добавить подключение к пБД'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SAVE_SQL','ru','Сохранить запрос в файл'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SETTINGS','ru','Открыть настройки'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_CREATE_UDB_WIZARD','ru','Открыть мастер создания пБД'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_UDB_VIEWER','ru','Открыть обзорщик пБД'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.APP_LANGUAGE.CAPTIONS','ru','Русский:Английский'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_FONT_SIZE.CAPTIONS','ru','Простой:Жирный');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('SETTINGS.TITLE','ru','Настройки'),
	 ('BUTTON.OK','ru','ОК'),
	 ('MAIN.MAIN_MENU.FILE.GENERATE','en','Generate'),
	 ('MAIN.MAIN_MENU.FILE.REFRESH','en','Refresh'),
	 ('MAIN.MAIN_MENU.FILE.CLEAR_ALL','en','Clear'),
	 ('BUTTON.SAVE','en','Save'),
	 ('MAIN.MAIN_MENU.CONNECTIONS.ADD_UDB','en','Add uDB-connection'),
	 ('MAIN.MAIN_MENU.CONNECTIONS.CREATE_UDB','en','Create new uDB...'),
	 ('MAIN.MAIN_MENU.CONNECTIONS.UDB_VIEWER','en','View all uDB''s...'),
	 ('MAIN.MAIN_MENU.FILE','en','File'),
	 ('MAIN.MAIN_MENU.CONNECTIONS','en','Connections'),
	 ('MAIN.MAIN_MENU.GENERATOR','en','Generator'),
	 ('MAIN.MAIN_MENU.GENERATOR.SIMPLE_GENERATORS','en','Simple generators'),
	 ('MAIN.MAIN_MENU.TOOLS','en','Tools'),
	 ('MAIN.MAIN_MENU.TOOLS.SETTINGS','en','Settings...'),
	 ('MAIN.TOOLBAR.SHORTHELP.GENERATE','en','Generate SQL-code'),
	 ('MAIN.TOOLBAR.SHORTHELP.CLEAR_ALL','en','Clear all fields'),
	 ('MAIN.TOOLBAR.SHORTHELP.REFRESH','en','Refresh uDB list'),
	 ('MAIN.TOOLBAR.SHORTHELP.SAVE_SQL','en','Save SQL-script'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.TABLE_NAME','en','Table name:'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.ROW_COUNT','en','Row count:'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_NAME','en','Column name'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_TYPE','en','Column type'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE','en','General'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE.CREATE_TABLE','en','CREATE TABLE'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE.ADD_ID','en','Add ID-column'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE.INIT_VALUE_ID','en','Initial ID'),
	 ('MAIN.MAIN_PANEL.TABLE_PAGE','en','Table'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE','en','Indexes'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.NEW_INDEX','en','New Index'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.DELETE_INDEX','en','Delete'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.INDEX_NAME','en','Name:'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.INDEX_COLUMNS','en','Columns:'),
	 ('MAIN.STATUSBAR.STATUS.WAITING','en','Waiting...'),
	 ('MAIN.STATUSBAR.STATUS.GENERATING','en','Generating...'),
	 ('MAIN.STATUSBAR.STATUS.DONE','en','Done'),
	 ('NEW_UDB_WIZARD.CANCEL_MESSAGE.MESSAGE','en','All entered data will inevitably be lost!'),
	 ('MESSAGE_BOX.CAPTION_APPROVE','en','Are you sure?'),
	 ('NEW_UDB_WIZARD.BUTTON.NEXT','en','Next ->'),
	 ('BUTTON.CANCEL','en','Cancel'),
	 ('NEW_UDB_WIZARD.BUTTON.PREVIOUS','en','<- Previous'),
	 ('NEW_UDB_WIZARD.BUTTON.FINISH','en','Finish'),
	 ('NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.MESSAGE','en','All fields must be filled in!'),
	 ('NEW_UDB_WIZARD.INFORMATION','en','This wizard is designed to create a working uDB framework'),
	 ('NEW_UDB_WIZARD.TITLE','en','uDB Creation Wizard'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.DB_PATH','en','DB path'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.DB_NAME','en','DB name'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.TITLE','en','Specify the name of the file to be created and the path where you want to save the file.'),
	 ('NEW_UDB_WIZARD.SECOND_PAGE.TITLE','en','Specify whether you want to add the created uDB to SQLDataForge.
Fill in all the fields if necessary.'),
	 ('NEW_UDB_WIZARD.SECOND_PAGE.ADD_IN_SDFORGE','en','Add in SQLDataForge');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('NEW_UDB_WIZARD.SECOND_PAGE.DB_ALIAS','en','Alias'),
	 ('NEW_UDB_WIZARD.SECOND_PAGE.DB_DESC','en','Description'),
	 ('NEW_UDB_WIZARD.THIRD_PAGE.INFO_TITLE','en','Information about file'),
	 ('NEW_UDB_WIZARD.THIRD_PAGE.INFO_ADDON','en','Additional information'),
	 ('NEW_UDB_WIZARD.THIRD_PAGE.INFO_CHECK','en','Check the correctness of the specified data.'),
	 ('NEW_UDB_WIZARD.FINISH.SUCCESS_MESSAGE.CAPTION','en','The uDB layout has been created!'),
	 ('NEW_UDB_WIZARD.FINISH.SUCCESS_MESSAGE.MESSAGE','en','The layout of the uDB was created in'),
	 ('NEW_UDB_WIZARD.NEXT_PAGE_MESSAGE.CAPTION','en','Fill in the fields'),
	 ('NEW_UDB_WIZARD.FIRST_PAGE.DIR_DIALOG','en','Choose a path...'),
	 ('MAIN.MAIN_PANEL.INDEX_PAGE.ENTER_CONDITION_HERE','en','-- Enter conditions here'),
	 ('MAIN.STATUSBAR.TIMER.GENERATE_TIME','en','Generated for:'),
	 ('MAIN.STATUSBAR.TIMER.ALL_TIME','en',' s., in total:'),
	 ('FILE_DIALOG.CAPTION_SAVE','en','Save as...'),
	 ('FILE_DIALOG.WILDCARD_DB','en','File DB SQLite (*.db)|*.db'),
	 ('MAIN.MESSAGE_BOX.SAVE_SCRIPT.FILE','en','File'),
	 ('MAIN.MESSAGE_BOX.SAVE_SCRIPT.SAVED','en',' saved in '),
	 ('MAIN.STATUSBAR.STATUS.SAVED','en','Saved'),
	 ('MAIN.MESSAGE_BOX.CLEAR_FORM.MESSAGE','en','Are you sure you want to clear all the fields?
The unsaved request will be deleted forever!'),
	 ('MAIN.MESSAGE_BOX.CLEAR_FORM.CAPTION','en','Confirmation of clearing fields'),
	 ('MAIN.MESSAGE_BOX.CLOSE_APP.MESSAGE','en','Are you sure you want to exit the app?'),
	 ('MAIN.MESSAGE_BOX.CLOSE_APP.CAPTION','en','Confirm the exit'),
	 ('MAIN.MESSAGE_BOX.INIT.MESSAGE1','en','Added new uDB''s:'),
	 ('MAIN.MESSAGE_BOX.INIT.MESSAGE2','en',', errors:'),
	 ('MAIN.MESSAGE_BOX.INIT.CAPTION','en','Update'),
	 ('CONNECTION_VIEWER.DB_DESC.HINT','en','There is no description...'),
	 ('CONNECTION_VIEWER.DB_TREE.LOCAL_UDB','en','local uDB''s'),
	 ('CONNECTION_VIEWER.DB_TREE.GLOBAL_UDB','en','global uDB''s'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_CONNECTION.MESSAGE','en','You cannot delete uDB''s from the local repository'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.CAPTION','en','Deletion error'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_SINGLE_CONNECTION.MESSAGE','en','There should be at least one uDB left!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_SINGLE_CONNECTION.CAPTION','en','Deletion error'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.SUCCESS_SAVE_CHANGES.MESSAGE','en','uDB has been successfully changed!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.SUCCESS_SAVE_CHANGES.CAPTION','en','Successful change'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.ERROR_SAVE_CHANGES.CAPTION','en','Saving error'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.CLOSE_ATTENTION.MESSAGE','en','Unsaved data will be deleted!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.CLOSE_ATTENTION.CAPTION','en','Are you sure you want to close the window?'),
	 ('CONNECTION_VIEWER.TITLE','en','Avaliable uDB'),
	 ('CONNECTION_VIEWER.DB_INFO','en','Information about uDB'),
	 ('CONNECTION_VIEWER.DB_NAME','en','Name:'),
	 ('CONNECTION_VIEWER.DB_ALIAS','en','Alias:'),
	 ('CONNECTION_VIEWER.DB_PATH','en','Path:'),
	 ('CONNECTION_VIEWER.DB_DESC','en','Description:'),
	 ('BUTTON.CLOSE','en','Close'),
	 ('FILE_DIALOG.CAPTION_CHOOSE','en','Choose a file...'),
	 ('NEW_CONN.MESSAGE_BOX.CLOSE.MESSAGE','en','The entered data will be deleted!'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_FALSE.CAPTION','en','Empty path'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_FALSE.MESSAGE','en','Enter the correct path to the uDB!'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.MESSAGE','en','The test connection is successful!'),
	 ('NEW_CONN.MESSAGE_BOX.TEST_CONN_TRUE.CAPTION','en','Successful connection'),
	 ('NEW_CONN.MESSAGE_BOX.WITHOUT_TEXT_CONN.MESSAGE','en','You are trying to add uDB''s without testing the connection!
To continue working, confirm the addition!');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('NEW_CONN.MESSAGE_BOX.WITHOUT_TEXT_CONN.CAPTION','en','Confirm the addition of uDB''s'),
	 ('NEW_CONN.MESSAGE_BOX.ADDING_UDB_TRUE.MESSAGE','en','uDB has been successfully added!'),
	 ('NEW_CONN.MESSAGE_BOX.ADDING_UDB_TRUE.CAPTION','en','Successful addition'),
	 ('NEW_CONN.TITLE','en','New connection'),
	 ('NEW_CONN.DB_NAME','en','Name of uDB:'),
	 ('NEW_CONN.DB_PATH','en','Path to uDB:'),
	 ('NEW_CONN.DB_DESC.HINT','en','Enter a description of the pBB...'),
	 ('NEW_CONN.DB_DESC','en','Description of uDB:'),
	 ('BUTTON.TEST','en','Test'),
	 ('BUTTON.APPLY','en','Apply'),
	 ('BUTTON.GENERATE','en','Generate'),
	 ('SINGLE_GENERATOR.ITER_COUNT','en','Count of iterations:'),
	 ('SINGLE_GENERATOR.OUTPUT','en','Output:'),
	 ('SINGLE_GENERATOR.TITLE','en','Simple Value Generator'),
	 ('SINGLE_GENERATOR.MESSAGE_BOX.ERROR_GENERATE.CAPTION','en','Value error'),
	 ('SINGLE_GENERATOR.MESSAGE_BOX.ERROR_GENERATE.MESSAGE','en','The values entered must be integers!
The first value must not be greater than or equal to the second value!'),
	 ('SINGLE_GENERATOR.GO_GENERATE','en','Generate a field'),
	 ('SINGLE_GENERATOR.SELECT_DB.SELECT_COUNT','en','Number of sample rows:'),
	 ('APP.SIMPLE_GEN.RAND_NUMBER.MINVALUE','en','Min. number:'),
	 ('APP.SIMPLE_GEN.RAND_NUMBER.MAXVALUE','en','Max. number:'),
	 ('APP.SIMPLE_GEN.RAND_NUMBER','en','Random number'),
	 ('APP.SIMPLE_GEN.RAND_DATE','en','Random date'),
	 ('APP.SETTINGS.THEME','en','Theme'),
	 ('APP.SETTINGS.THEME.GENERAL','en',''),
	 ('APP.SETTINGS.THEME.REDACTOR','en','SQL Redactor'),
	 ('APP.SETTINGS.SYSTEM','en','System'),
	 ('APP.SETTINGS.SYSTEM.GENERAL','en','General'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS','en','Hotkeys'),
	 ('APP.SETTINGS.SYSTEM.PARAMETERS','en','Parameters'),
	 ('APP.SETTINGS.SYSTEM.REDACTOR.FONT_COLOR','en','Font color'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.IS_CATCH_CLOSING_APP','en','Require confirmation to exit'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_WORD','en','Color of keywords:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_COMMENT','en','Color of commentaries:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_NUMBER','en','Color of numbers:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_FONT_SIZE','en','Font size:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_STRING','en','Color of strings:'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_FONT_BOLD','en','Font type:'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.FORMAT_DATE','en','Date column:'),
	 ('APP.SETTINGS.SYSTEM.REDACTOR.FONT_SETTINGS','en','Font settings'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.TABLE_TITLE','en','Description:Hotkey'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.APP_SETTINGS','en','App settings'),
	 ('APP.SETTINGS.SYSTEM.GENERAL.APP_LANGUAGE','en','Language:'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_EXECUTE','en','Generate SQL-query'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_CLEAR_ALL','en','Clean all fields'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_REFRESH','en','Refresh the uDB tree'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_NEW_INSTANCE','en','Add connection on uDB'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SAVE_SQL','en','Save SQL-query in file'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SETTINGS','en','Open settings'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_CREATE_UDB_WIZARD','en','Open wizard for creating uDB'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_UDB_VIEWER','en','Open the uDB viewer');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('APP.SETTINGS.SYSTEM.GENERAL.APP_LANGUAGE.CAPTIONS','en','Russian:English'),
	 ('APP.SETTINGS.THEME.REDACTOR.STC_FONT_SIZE.CAPTIONS','en','Normal:Bold'),
	 ('SETTINGS.TITLE','en','Settings'),
	 ('BUTTON.OK','en','OK'),
	 ('E001.CAPTION','ru','Пустой запрос'),
	 ('E002.CAPTION','ru','Неизвестный параметр'),
	 ('E003.CAPTION','ru','Не выбрана таблица'),
	 ('E004.CAPTION','ru','Не указано имя таблицы'),
	 ('E005.CAPTION','ru','Не указано количество записей'),
	 ('E006.CAPTION','ru','Некорректное значение количества строк'),
	 ('E010.CAPTION','ru','Ошибка исходной таблицы'),
	 ('E007.CAPTION','ru','Одинаковые имена столбцов'),
	 ('E008.CAPTION','ru','Не указано имя индекса'),
	 ('E009.CAPTION','ru','Не выбрано ни одного столбца'),
	 ('E011.CAPTION','ru','Одинаковые имена индексов'),
	 ('E012.CAPTION','ru','Неисправная пБД'),
	 ('E013.CAPTION','ru','Некорректное заполнение таблицы t_cases_info'),
	 ('E014.CAPTION','ru','Повреждение сБД'),
	 ('E001.MESSAGE','ru','Сгенерируйте SQL-запрос!'),
	 ('E002.MESSAGE','ru','Параметр подстановки не найден!'),
	 ('E003.MESSAGE','ru','Введите хотя бы одну таблицу!'),
	 ('E004.MESSAGE','ru','Введите имя таблицы, в которую будут вноситься данные!'),
	 ('E005.MESSAGE','ru','Укажите, сколько будет сгенерировано строк данных!'),
	 ('E006.MESSAGE','ru','Проверьте значение, указанное для количества генерируемых строк!'),
	 ('E010.MESSAGE','ru','Проверьте заполненность таблицы исходных данных пБД! Скорее всего, данные отсутствуют.'),
	 ('E007.MESSAGE','ru','Проверьте имена столбцов, они должны быть уникальными!'),
	 ('E008.MESSAGE','ru','Проверьте индексы, у каждого индекса должно быть указано имя!'),
	 ('E009.MESSAGE','ru','Проверьте индексы, у каждого индекса должен быть указан хотя-бы один столбец!'),
	 ('E011.MESSAGE','ru','Проверьте имена индексов, они должны быть уникальными!'),
	 ('E012.MESSAGE','ru','Проверьте структуру пользовательской Базы Данных!'),
	 ('E013.MESSAGE','ru','Проверьте состояние таблицы t_cases_info в пользовательской Базе Данных!'),
	 ('E014.MESSAGE','ru','Системная База Данных была повреждена! Восстановите сБД до исходного состояния!'),
	 ('E001.CAPTION','en','An empty request'),
	 ('E002.CAPTION','en','Unknown parameter'),
	 ('E003.CAPTION','en','No table selected'),
	 ('E004.CAPTION','en','The table name is not specified'),
	 ('E005.CAPTION','en','The number of entries is not specified'),
	 ('E006.CAPTION','en','Incorrect value of the number of rows'),
	 ('E010.CAPTION','en','Source table error'),
	 ('E007.CAPTION','en','Identical column names'),
	 ('E008.CAPTION','en','The index name is not specified'),
	 ('E009.CAPTION','en','No columns are selected'),
	 ('E011.CAPTION','en','The same index names'),
	 ('E012.CAPTION','en','Faulty uDB'),
	 ('E013.CAPTION','en','Incorrect filling of "t_cases_info" table'),
	 ('E014.CAPTION','en','Damage to the sDB'),
	 ('E001.MESSAGE','en','Generate an SQL query!'),
	 ('E002.MESSAGE','en','The substitution parameter was not found!'),
	 ('E003.MESSAGE','en','Enter at least one table!'),
	 ('E004.MESSAGE','en','Enter the name of the table to which the data will be entered!');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('E005.MESSAGE','en','Specify how many rows of data will be generated!'),
	 ('E006.MESSAGE','en','Check the value specified for the number of rows to be generated!'),
	 ('E010.MESSAGE','en','Check the completeness of the uDB source data table! Most likely, there is no data available.'),
	 ('E007.MESSAGE','en','Check the column names, they must be unique!'),
	 ('E008.MESSAGE','en','Check the indexes, each index must have a name!'),
	 ('E009.MESSAGE','en','Check the indexes, each index must have at least one column specified!'),
	 ('E011.MESSAGE','en','Check the index names, they must be unique!'),
	 ('E012.MESSAGE','en','Check the structure of the user Database!'),
	 ('E013.MESSAGE','en','Check the status of the "t_cases_info" table in the user Database!'),
	 ('E014.MESSAGE','en','The System Database has been corrupted! Restore the sDB to its original state!'),
	 ('SETTINGS.MESSAGE_BOX.CLOSE.ALL_CLEAR','ru','Все несохраненные изменения будут удалены!'),
	 ('SETTINGS.MESSAGE_BOX.CLOSE.ALL_CLEAR','en','All unsaved changes will be deleted!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.MESSAGE','ru','Невозможно удалить локальную пБД!'),
	 ('CONNECTION_VIEWER.MESSAGE_BOX.DROP_LOCAL_CONNECTION.MESSAGE','en','It is impossible to delete the local pBB!'),
	 ('SETTINGS.RESTART_FOR_APPLY_CHANGES.MESSAGE','ru','Для применения всех изменений требуется перезапуск приложения!
Перезапустить сейчас?'),
	 ('SETTINGS.RESTART_FOR_APPLY_CHANGES.CAPTION','ru','Подтвердите действие'),
	 ('SETTINGS.RESTART_FOR_APPLY_CHANGES.MESSAGE','en','Restarting the application is required to apply all changes!
Restart now?'),
	 ('SETTINGS.RESTART_FOR_APPLY_CHANGES.CAPTION','en','Confirm the action'),
	 ('RECOVERY.TITLE','ru','Восстановление'),
	 ('RECOVERY.TITLE','en','Recovery'),
	 ('RECOVERY.HEADER','ru','Модуль восстановления'),
	 ('RECOVERY.HEADER2','ru','Данный модуль исправляет причины возникновения ошибок'),
	 ('RECOVERY.CHOOSE_ACTION','ru','Укажите необходимое действие:'),
	 ('MAIN.MAIN_MENU.TOOLS.RECOVERY','ru','Восстановление'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.RECOVERY','ru','Открыть модуль восстановления'),
	 ('RECOVERY.ACTIONS','ru','Сброс системной БД'),
	 ('BUTTON.DO','ru','Выполнить'),
	 ('RECOVERY.ACTIONS','en','Resetting the system DB'),
	 ('RECOVERY.HEADER','en','Recovery unit'),
	 ('RECOVERY.HEADER2','en','This module corrects the causes of errors'),
	 ('RECOVERY.ACTIONS','en','Specify the required action:'),
	 ('BUTTON.DO','en','GO'),
	 ('MAIN.MAIN_MENU.TOOLS.RECOVERY','en','Recovery'),
	 ('MAIN.MAIN_MENU.TOOLS.LOGVIEWER','ru','Просмотр логов'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_LOGVIEWER','ru','Просмотреть логи'),
	 ('LOGVIEWER.ERROR_LOG','ru','Ошибки'),
	 ('LOGVIEWER.EXECUTION_LOG','ru','SQL-запросы'),
	 ('LOGVIEWER.ERROR_LOG.HEADER.ERROR_CODE','ru','Код ошибки'),
	 ('LOGVIEWER.ERROR_LOG.HEADER.ERROR_CAPTION','ru','Описание ошибки'),
	 ('LOGVIEWER.ERROR_LOG.HEADER.ERROR_CATCHED','ru','Выброс ошибки'),
	 ('MAIN.MAIN_MENU.INFO','ru','Справка'),
	 ('MAIN.MAIN_MENU.INFO.ABOUT_APP','ru','О программе...'),
	 ('BUTTON.SAVE_AS','ru','Сохранить как...'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SAVE_AS','ru','Сохранить в новом файле'),
	 ('FILE_DIALOG.WILDCARD_SQL','ru','Файл SQL (*.sql)|*.sql'),
	 ('FILE_DIALOG.WILDCARD_SQL','en','SQL script (*.sql)|*.sql'),
	 ('MAIN.MAIN_MENU.TOOLS.LOGVIEWER','en','Log viewer'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_LOGVIEWER','en','View the log table'),
	 ('LOGVIEWER.ERROR_LOG','en','Errors'),
	 ('LOGVIEWER.EXECUTION_LOG','en','SQL-scripts'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_LABEL','ru','Псевдоним столбца'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.NOT_NULL','ru','Не пустой'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.UNIQUE','ru','Уникальный'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.COLUMN_LABEL','en','Column alias'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.NOT_NULL','en','NOT NULL'),
	 ('MAIN.MAIN_PANEL.MAIN_PAGE.UNIQUE','en','UNIQUE');
/
INSERT INTO t_lang_text (label,lang,text) VALUES
	 ('LOGVIEWER.ERROR_LOG.HEADER.ERROR_CODE','en','Error code'),
	 ('LOGVIEWER.ERROR_LOG.HEADER.ERROR_CAPTION','en','Error desc'),
	 ('LOGVIEWER.ERROR_LOG.HEADER.ERROR_CATCHED','en','Error handled'),
	 ('MAIN.MAIN_MENU.INFO','en','Help'),
	 ('MAIN.MAIN_MENU.INFO.ABOUT_APP','en','About the program...'),
	 ('BUTTON.SAVE_AS','en','Save as...'),
	 ('APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SAVE_AS','en','Save in new file');
/
INSERT INTO t_err_codes (err_code,title,message) VALUES
	 ('E001','E001.CAPTION','E001.MESSAGE'),
	 ('E002','E002.CAPTION','E002.MESSAGE'),
	 ('E003','E003.CAPTION','E003.MESSAGE'),
	 ('E004','E004.CAPTION','E004.MESSAGE'),
	 ('E005','E005.CAPTION','E005.MESSAGE'),
	 ('E006','E006.CAPTION','E006.MESSAGE'),
	 ('E010','E010.CAPTION','E010.MESSAGE'),
	 ('E007','E007.CAPTION','E007.MESSAGE'),
	 ('E008','E008.CAPTION','E008.MESSAGE'),
	 ('E009','E009.CAPTION','E009.MESSAGE'),
	 ('E011','E011.CAPTION','E011.MESSAGE'),
	 ('E012','E012.CAPTION','E012.MESSAGE'),
	 ('E013','E013.CAPTION','E013.MESSAGE'),
	 ('E014','E014.CAPTION','E014.MESSAGE'),
	 ('E015','E015.CAPTION','E015.MESSAGE');
/
INSERT INTO t_params (param_name,param_value,param_type,param_label,update_layout) VALUES
	 ('RDate.today','datetime.datetime.now().date()','GEN',NULL,NULL),
	 ('IS_CATCH_CLOSING_APP','False','SYSTEM',NULL,0),
	 ('STC_COLOUR_WORD','#9200F2','SYSTEM',NULL,1),
	 ('STC_COLOUR_COMMENT','#009','SYSTEM',NULL,1),
	 ('STC_COLOUR_NUMBER','#1017FF','SYSTEM',NULL,1),
	 ('STC_COLOUR_STRING','#56A222','SYSTEM',NULL,1),
	 ('STC_FONT_SIZE','10','SYSTEM',NULL,1),
	 ('STC_FONT_BOLD','400','SYSTEM',NULL,1),
	 ('KEY_EXECUTE','F9','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_EXECUTE',0),
	 ('KEY_CLEAR_ALL','F3','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_CLEAR_ALL',0),
	 ('KEY_REFRESH','F5','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_REFRESH',0),
	 ('KEY_NEW_INSTANCE','Shift+Ctrl+F5','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_NEW_INSTANCE',0),
	 ('KEY_SAVE_SQL','Ctrl+S','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SAVE_SQL',0),
	 ('KEY_SETTINGS','','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SETTINGS',0),
	 ('KEY_CREATE_UDB_WIZARD','','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_CREATE_UDB_WIZARD',0),
	 ('KEY_UDB_VIEWER','','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_UDB_VIEWER',0),
	 ('FORMAT_DATE','%d-%m-%Y','SYSTEM',NULL,0),
	 ('APP_LANGUAGE','ru','SYSTEM',NULL,2),
	 ('KEY_RECOVERY','','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.RECOVERY',0),
	 ('KEY_LOGVIEWER','','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_LOGVIEWER',0),
	 ('KEY_SAVE_AS','Ctrl+Shift+S','HOTKEY','APP.SETTINGS.SYSTEM.HOTKEYS.KEY_SAVE_AS',0);
/
INSERT INTO t_settings_items (id_fk,sett_label,is_valid) VALUES
	 (NULL,'APP.SETTINGS.THEME','Y'),
	 (1,'APP.SETTINGS.THEME.GENERAL','N'),
	 (1,'APP.SETTINGS.THEME.REDACTOR','Y'),
	 (NULL,'APP.SETTINGS.SYSTEM','Y'),
	 (4,'APP.SETTINGS.SYSTEM.GENERAL','Y'),
	 (4,'APP.SETTINGS.SYSTEM.HOTKEYS','Y'),
	 (4,'APP.SETTINGS.SYSTEM.PARAMETERS','N');
/
INSERT INTO t_settings_items_params (id_param,id_parent,posid,entry_type,entry_label,entry_choices,entry_label_choices,is_valid) VALUES
	 (3,5,3,'CheckboxPoint','APP.SETTINGS.SYSTEM.GENERAL.IS_CATCH_CLOSING_APP',NULL,NULL,'Y'),
	 (NULL,3,1,'HeaderGroup','APP.SETTINGS.SYSTEM.REDACTOR.FONT_COLOR',NULL,NULL,'Y'),
	 (4,3,2,'HEXEnter','APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_WORD',NULL,NULL,'Y'),
	 (5,3,3,'HEXEnter','APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_COMMENT',NULL,NULL,'Y'),
	 (6,3,4,'HEXEnter','APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_NUMBER',NULL,NULL,'Y'),
	 (NULL,3,6,'HeaderGroup','APP.SETTINGS.SYSTEM.REDACTOR.FONT_SETTINGS',NULL,NULL,'Y'),
	 (8,3,7,'SpinNumber','APP.SETTINGS.THEME.REDACTOR.STC_FONT_SIZE','6:20',NULL,'Y'),
	 (7,3,5,'HEXEnter','APP.SETTINGS.THEME.REDACTOR.STC_COLOUR_STRING',NULL,NULL,'Y'),
	 (9,3,8,'SelectorBox','APP.SETTINGS.THEME.REDACTOR.STC_FONT_BOLD','400:700','APP.SETTINGS.THEME.REDACTOR.STC_FONT_SIZE.CAPTIONS','Y'),
	 (NULL,3,9,'CodeRedactor',NULL,'UPDATE t_persons as p\nSET    p.age = 18\nWHERE  p.first_name = ''Smith''; -- Only one Smith on this table :)',NULL,'Y'),
	 (NULL,6,1,'TableSystemColumns','APP.SETTINGS.SYSTEM.HOTKEYS.TABLE_TITLE','SELECT p.param_name, lt.text, p.param_value FROM t_params p, t_lang_text lt WHERE p.param_type = ''HOTKEY'' AND p.param_label = lt.label AND lt.lang = ''$0'';',NULL,'Y'),
	 (NULL,5,1,'HeaderGroup','APP.SETTINGS.SYSTEM.GENERAL.APP_SETTINGS',NULL,NULL,'Y'),
	 (17,5,4,'MaskedTextEntry','APP.SETTINGS.SYSTEM.GENERAL.FORMAT_DATE',NULL,NULL,'Y'),
	 (18,5,2,'SelectorBox','APP.SETTINGS.SYSTEM.GENERAL.APP_LANGUAGE','ru:en','APP.SETTINGS.SYSTEM.GENERAL.APP_LANGUAGE.CAPTIONS','Y');
/
INSERT INTO t_simple_gen (gen_code,gen_name,gen_type,generator,is_valid) VALUES
	 ('rand_number','APP.SIMPLE_GEN.RAND_NUMBER','simple','random.randint($1, $2)','Y'),
	 ('rand_date','APP.SIMPLE_GEN.RAND_DATE','simple',NULL,'N');
/
INSERT INTO t_simple_gen_entries (id_field,posid,entry_name,entry_type) VALUES
	 (1,1,'APP.SIMPLE_GEN.RAND_NUMBER.MINVALUE','TextCtrl'),
	 (1,2,'APP.SIMPLE_GEN.RAND_NUMBER.MAXVALUE','TextCtrl');
/