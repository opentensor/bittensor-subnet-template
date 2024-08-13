from abc import ABC, abstractmethod


class SerializableManager(ABC):

    @abstractmethod
    def get_state(self) -> dict:
        pass

    @abstractmethod
    def set_state(self, state: dict):
        pass
