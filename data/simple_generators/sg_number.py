import random

class GeneratorNumber:

    @staticmethod
    def generate(*args):
        return random.randint(int(args[0]), int(args[1]))