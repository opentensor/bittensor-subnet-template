from typing import Any
from abc import abstractmethod

from numpy import ndarray
import numpy as np
from pydantic import BaseModel, field_serializer


class ModelEvaluationResult(BaseModel):
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    fbeta: float = 0.0
    confusion_matrix: list = [[0, 0], [0, 0]]
    fpr: list = []
    tpr: list = []
    roc_auc: float = 0.0
    run_time_s: float = 0.0
    tested_entries: int = 0

    score: float = 0.0

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
