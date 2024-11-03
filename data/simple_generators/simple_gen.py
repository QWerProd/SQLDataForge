import os
import json
import sqlite3

from app_parameters import APPLICATION_PATH


class SimpleDataFromDBGenerator:

    gen_code: str
    generator: object
    app_conn: sqlite3.Connection
    
    def __init__(self, gen_code: str, is_use_default: None):
        from sql_generator import SQLGenerator

        self.gen_code = gen_code
        self.app_conn = sqlite3.connect(os.path.join(APPLICATION_PATH, 'app/app.db'))
        self.generator = SQLGenerator(self.app_conn, 1, self.gen_code.split(':'), [self.gen_code.split(':')[1], ],
                                      is_format_columns=False, is_simple_mode=True)
        self.gen_code = gen_code

    def get_data_type(self) -> None:
        pass
    
    def generate(self, rows_count: int, params: list = []) -> list:
        gen_data = self.generator.GenerateValues(rows_count=rows_count)
        for val in gen_data.values():
            ret = val
        return ret


class SimpleDataFromInputGenerator:

    gen_code: str
    generator_class: object
    req_params: int
    validate: bool
    is_use_default: bool
    
    def __init__(self, gen_code: str, is_use_default: bool = False):
        self.gen_code = gen_code
        self.is_use_default = is_use_default
        
        # Чтение JSON с простыми генераторами
        simple_generators = []
        with open(os.path.join(APPLICATION_PATH, 'data/simple_generators/simple_gens.json')) as json_file:
            simple_generators = json.load(json_file)
        
        # Импорт и инициализация нужного класса
        for gen_object in simple_generators:
            if gen_object['gen_code'] == gen_code:
                class_name = gen_object['class_name']
                imported_module = __import__('data.simple_generators.%s' % gen_object['module_name'], 
                                              fromlist=(class_name,))
                self.generator_class = getattr(imported_module, class_name)
                self.req_params = gen_object['required_params']
                self.validate = gen_object['validate']
                break

    def get_data_type(self) -> str:
        return self.generator_class.get_data_type()
    
    def generate(self, rows_count: int, params: list = []) -> list:
        if not self.is_use_default:
            if self.req_params != len(params):
                raise RequiredDataMissedError(str(self.req_params), str(len(params)))
        
        is_valid = True
        if not self.is_use_default:
            if self.validate:
                is_valid = self.generator_class.validate(*params)
        
        if not is_valid:
            raise ValidationParamsError()

        ret = []
        try:
            for i in range(rows_count):
                temp = self.generator_class.generate(*params)
                ret.append(str(temp))
        except ValueError:
            raise InvalidParamsError
        
        return ret


class ControllerSimpleGenerator:
    """Контроллер простых генераторов
       Запускает разные типы генераторов
       
    Args:
        gen_type (str ('user_input' | 'user_db')): тип генератора (пользовательский | из пБД)
        gen_code (str): Код генератора
        params (list, optional): Дополнительные параметры (для 'user_input'). Defaults to ().
    """

    generator = object
    gen_types = {
        "user_input": SimpleDataFromInputGenerator,
        "user_db": SimpleDataFromDBGenerator
    }
    gen_code = str
    params = list
    is_use_default = bool

    def __init__(self, gen_type: str, gen_code: str, params: list = (), is_use_default: bool = False) -> None:
        self.gen_code = gen_code
        self.params = params
        self.is_use_default = is_use_default
        self.generator = self.gen_types.get(gen_type)(self.gen_code, is_use_default)

    def get_data_type(self) -> str:
        return self.generator.get_data_type()

    def generate(self, row_count: int) -> list:
        return self.generator.generate(row_count, self.params)


############################################################
### Exceptions
############################################################

class RequiredDataMissedError(BaseException):

    req_entries: str
    gived_entries: str
    
    def __init__(self, requeired_entries: str, gived_entries: str) -> None:
        super().__init__()
        self.req_entries = requeired_entries
        self.gived_entries = gived_entries

    def __str__(self) -> str:
        return 'to generate data need to pass %s parameters, given %s parameters', (self.req_entries, self.gived_entries)


class InvalidParamsError(BaseException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return 'the entered data does not match the required type'
    

class ValidationParamsError(BaseException):
    def __init__(self) -> None:
        super().__init__()
    
    def __str__(self) -> str:
        return 'set of parameters has not passed the validation before generation'