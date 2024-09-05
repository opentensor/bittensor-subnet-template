from typing import Any
from abc import abstractmethod

from numpy import ndarray
from pydantic import BaseModel


class ModelEvaluationResult(BaseModel):
    accuracy: float
    precision: float
    recall: float
    confusion_matrix: ndarray
    fpr: ndarray
    tpr: ndarray
    roc_auc: float
    run_time_s: float
    tested_entries: int

    class Config:
        arbitrary_types_allowed = True


class BaseCompetitionHandler:
    """
    Base class for handling different competition types.

    This class initializes the config and competition_id attributes.
    """

    def __init__(self, X_test: list, y_test: list) -> None:
        """
        Initializes the BaseCompetitionHandler object.
        """
        self.X_test = X_test
        self.y_test = y_test

    @abstractmethod
    def preprocess_data(self):
        """
        Abstract method to prepare the data.

        This method is responsible for preprocessing the data for the competition.
        """

    @abstractmethod
    def get_model_result(self) -> ModelEvaluationResult:
        """
        Abstract method to evaluate the competition.

        This method is responsible for evaluating the competition.
        """
