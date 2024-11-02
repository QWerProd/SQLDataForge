import string
import secrets

class GeneratorPassword:

    @staticmethod
    def get_data_type() -> str:
        return 'text-value'

    @staticmethod
    def validate(length: str = '8', is_digits: str = 'False') -> bool:
        return True if length.isdigit() and (is_digits == 'True' or is_digits == 'False') else False

    @staticmethod
    def generate(length: str = '8', is_digits: str = 'False') -> str:
        password = ''
        alphabet = string.ascii_letters
        if is_digits == 'True': alphabet += string.digits

        password = ''.join(secrets.choice(alphabet) for i in range(int(length)))
        return password