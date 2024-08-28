from abc import abstractmethod

from dataclasses import dataclass

@dataclass
class ModelEvaluationResult:
    accuracy: float
    precision: float
    recall: float
    confusion_matrix: any
    fpr: any
    tpr: any
    roc_auc: float
    run_time: float
    tested_entries: int

class BaseCompetitionHandler:
    """
    Base class for handling different competition types.

    This class initializes the config and competition_id attributes.
    """

    def __init__(self, X_test, y_test) -> None:
        """
        Initializes the BaseCompetitionHandler object.

        Args:
            X_test (list): List of test images.
            y_test (list): List of test labels.
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