
class c:
    dotenv = {}

    @staticmethod
    def get(obj, path, default):
        return Utils.get(c.dotenv, path, default)

