from abc import abstractmethod

class BaseRunnerHandler:
    def __init__(self, config, model_path: str) -> None:
        self.config = config
        self.model_path = model_path

    @abstractmethod
    def run(self):
        """Exceutes the run process of the model in separate process."""
