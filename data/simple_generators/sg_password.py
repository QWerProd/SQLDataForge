import string
import secrets

class GeneratorPassword:

    @staticmethod
    def generate(length: str = '8', is_digits: str = 'False'):
        password = ''
        alphabet = string.ascii_letters
        if is_digits == 'True': alphabet += string.digits

        password = ''.join(secrets.choice(alphabet) for i in range(int(length)))
        return password