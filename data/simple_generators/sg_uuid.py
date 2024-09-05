import uuid


class GeneratorUUID:

    @staticmethod
    def validate(version: str = '4', param: str = None) -> bool:
        params = {
            '1': False,
            '3': True,
            '4': False,
            '5': True
        }

        need_param = params.get(version)
        return True if need_param is not None and need_param == bool(param) else False

    @staticmethod
    def generate(version: str = '4', param: str = None) -> str:
        res: str

        match version:
            case '1':
                res = uuid.uuid1()
            case '3':
                res = uuid.uuid3(uuid.NAMESPACE_DNS, param)
            case '4':
                res = uuid.uuid4()
            case '5':
                res = uuid.uuid5(uuid.NAMESPACE_DNS, param)
            
        return str(res)
            