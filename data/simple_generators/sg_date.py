import random as rd
from datetime import datetime, timedelta


class GeneratorDate:

    @staticmethod
    def generate(min_str_date: str, max_str_date: str, format_date: str = '%d.%m.%Y'):
        min_date = datetime.strptime(min_str_date, '%Y-%m-%d')
        max_date = datetime.strptime(max_str_date, '%Y-%m-%d')

        days = (datetime(max_date.year, max_date.month, max_date.day) - datetime(min_date.year, min_date.month, min_date.day)).days
        rnd_day = rd.randint(0, days)

        gen_date = datetime.strftime(min_date + timedelta(days=rnd_day), format_date)
        return gen_date