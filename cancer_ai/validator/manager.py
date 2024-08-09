

class SerializableManager:
    def __init__(self, config) -> None:
        self.config = config

    def get_state(self) -> dict:
        raise NotImplementedError
    
    def set_state(self, state: dict):
        raise NotImplementedError