from conversationgenome.Utils import Utils

class c:
    dotenv = {
        "validator" : {
            "miners_per_window": 3,
        }
    }

    @staticmethod
    def get(section, key, default):
        return Utils.get(section, key, default)

