import uuid


class GeneratorUUID:

    @staticmethod
    def generate(version: str = '4', param: str = None) -> uuid.UUID:
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
            
        return res
            