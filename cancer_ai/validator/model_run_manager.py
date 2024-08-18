from .manager import SerializableManager
from .model_manager import ModelInfo
from typing import List, Tuple
from abc import abstractmethod
from .utils import detect_model_format, ModelType


class BaseRunnerHandler:
    def __init__(self, config, model_path: str) -> None:
        self.config = config
        self.model_path = model_path

    @abstractmethod
    def run(self):
        """Exceutes the run process of the model in separate process."""


class PytorchRunnerHandler(BaseRunnerHandler):
    def run(self, pred_x: List, pred_y: List) -> List:
        # example, might not work
        from torch import load

        model = load(self.model_path)
        model.eval()
        output = model(pred_x)
        return output


runner_handler_mapping = {
    ModelType.PYTORCH: PytorchRunnerHandler,
}


class ModelRunManager(SerializableManager):
    def __init__(self, config, model: ModelInfo) -> None:
        self.config = config
        self.model = model

    def get_state(self) -> dict:
        return {}

    def set_state(self, state: dict):
        pass

    def set_runner_handler(self) -> None:
        self.handler = runner_handler_mapping[detect_model_format(self.model)](
            self.config, self.model.file_path
        )

    def run(self, pred_x: List) -> List:
        return self.handler.run(pred_x)
