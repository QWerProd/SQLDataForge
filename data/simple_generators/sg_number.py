import random

class GeneratorNumber:

    @staticmethod
    def validate(min_value: str, max_value: str):
        return True if int(min_value) < int(max_value) else False

    @staticmethod
    def generate(min_value: str, max_value: str):
        return random.randint(int(min_value), int(max_value))