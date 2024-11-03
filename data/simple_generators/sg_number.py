import random

class GeneratorNumber:

    @staticmethod
    def get_data_type() -> str:
        return 'integer-value'

    @staticmethod
    def validate(min_value: str, max_value: str):
        return True if int(min_value) < int(max_value) else False

    @staticmethod
    def generate(min_value: str = '0', max_value: str = '244140625'):
        return random.randint(int(min_value), int(max_value))