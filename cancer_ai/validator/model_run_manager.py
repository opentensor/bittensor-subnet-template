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


class TensorflowRunnerHandler(BaseRunnerHandler):
    def run(self, pred_x: List) -> List:
        return []


class PytorchRunnerHandler(BaseRunnerHandler):
    def run(self, pred_x: List) -> List:
        # example, might not work
        from torch import load

        model = load(self.model_path)
        model.eval()
        output = model(pred_x)
        return output


MODEL_TYPE_HANDLERS = {
    ModelType.PYTORCH: PytorchRunnerHandler,
    ModelType.TENSORFLOW_SAVEDMODEL: TensorflowRunnerHandler,
}


class ModelRunManager(SerializableManager):
    def __init__(self, config, model: ModelInfo) -> None:
        self.config = config
        self.model = model
        self.set_runner_handler()

    def get_state(self) -> dict:
        return {}

    def set_state(self, state: dict):
        pass

    def set_runner_handler(self) -> None:
        model_type = detect_model_format(self.model)
        # initializing ml model handler object
        model_handler = MODEL_TYPE_HANDLERS[model_type]
        self.handler = model_handler(self.config, self.model.file_path)

    def run(self, pred_x: List) -> List:
        """
        Run the model with the given input.

        Returns:
            List: model predictions
        """

        model_predictions = self.handler.run(pred_x)
        return model_predictions
