import time
import random
from typing import List

import bittensor as bt

from .manager import SerializableManager
from .model_manager import ModelManager, ModelInfo
from .dataset_manager import DatasetManager
from .model_run_manager import ModelRunManager

from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, roc_curve, auc
from dataclasses import dataclass

COMPETITION_MAPPING = {
    "melaona-1": "melanoma",
}


class ImagePredictionCompetition:
    def score_model(
        self, model_info: ModelInfo, pred_y: List, model_pred_y: List
    ) -> float:
        pass

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
    

class CompetitionManager(SerializableManager):
    """
    CompetitionManager is responsible for managing a competition.

    It handles the scoring, model management and synchronization with the chain.
    """

    def __init__(
        self,
        config,
        competition_id: str,
        category: str,
        evaluation_times: list[str],
        dataset_hf_id: str,
        file_hf_id: str,
    ) -> None:
        """
        Initializes a CompetitionManager instance.

        Args:
        config (dict): Config dictionary.
        competition_id (str): Unique identifier for the competition.
        category (str): Category of the competition.
        evaluation_time (list[str]): List of times of a day at which the competition will be evaluated in XX:XX format.

        Note: Times are in UTC time.
        """
        bt.logging.info(f"Initializing Competition: {competition_id}")
        self.config = config
        self.competition_id = competition_id
        self.category = category
        self.model_manager = ModelManager(config)

        # self.evaluation_time = [
        #     time(hour_min.split(":")[0], hour_min.split(":")[1])
        #     for hour_min in evaluation_times
        # ]
        self.dataset_manager = DatasetManager(
            config, competition_id, dataset_hf_id, file_hf_id
        )
        # self.model_evaluator =
        self.results = []

    def get_state(self):
        return {
            "competition_id": self.competition_id,
            "model_manager": self.model_manager.get_state(),
            "category": self.category,
            "evaluation_time": self.evaluation_time,
        }

    def set_state(self, state: dict):
        self.competition_id = state["competition_id"]
        self.model_manager.set_state(state["model_manager"])
        self.category = state["category"]
        self.evaluation_time = state["evaluation_time"]

    async def get_miner_model(self, hotkey):
        # TODO get real data
        return ModelInfo("safescanai/test_dataset", "melanoma.keras")

    async def init_evaluation(self):
        # TODO get models from chain
        miner_models = [
            # {
            #     "hotkey": "wojtasy",
            #     "hf_id": "safescanai/test_dataset",
            #     "file_hf_id": "melanoma.keras",
            # },
            # {
            #     "hotkey": "wojtasyy",
            #     "hf_id": "safescanai/test_dataset",
            #     "file_hf_id": "melanoma.keras",
            # },
            {
                "hotkey": "obcy ludzie",
                "hf_id": "safescanai/test_dataset",
                "file_hf_id": "simple_cnn_model.onnx",
            },
        ]
        bt.logging.info(
            f"Populating model manager with miner models. Got {len(miner_models)} models"
        )
        for miner_info in miner_models:
            self.model_manager.add_model(
                miner_info["hotkey"], miner_info["hf_id"], miner_info["file_hf_id"]
            )
        bt.logging.info("Initializing dataset")
        await self.dataset_manager.prepare_dataset()

        # log event

    async def evaluate(self):
        from PIL import Image
        import numpy as np
        await self.init_evaluation()
        path_X_test, y_test = await self.dataset_manager.get_data()
        # Prepre X_test form paths to images
        X_test = []
        target_size=(224, 224) #TODO: Change this to the correct size 

        for img_path in path_X_test:
            img = Image.open(img_path)
            img = img.resize(target_size)
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.array(img)  
            if img_array.shape[-1] != 3:    # Handle grayscale images
                img_array = np.stack((img_array,) * 3, axis=-1)
            
            img_array = np.transpose(img_array, (2, 0, 1))           # Convert image to numpy array
            img_array = np.expand_dims(img_array, axis=0)            # Add batch dimension
            X_test.append(img_array)
        X_test = np.array(X_test, dtype=np.float32)

        # print("X_test shape: ", X_test.shape)

        # map y_test to 0, 1
        y_test = [1 if y == "True" else 0 for y in y_test]

        for hotkey in self.model_manager.hotkey_store:
            bt.logging.info("Evaluating hotkey: ", hotkey)
            await self.model_manager.download_miner_model(hotkey)

            start_time = time.time()
            model_manager = ModelRunManager(
                self.config, self.model_manager.hotkey_store[hotkey]
            )
            y_pred = model_manager.run(X_test)
            print("Model prediction ", y_pred)
            print("Ground truth: ", y_test)
            # print "make stats and send to wandb"
            run_time = time.time() - start_time
            tested_entries = len(y_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            conf_matrix = confusion_matrix(y_test, y_pred)
            fpr, tpr, _ = roc_curve(y_test, y_pred)
            roc_auc = auc(fpr, tpr)

            model_result = ModelEvaluationResult(
                tested_entries=tested_entries,  
                run_time=run_time,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                confusion_matrix=conf_matrix,
                fpr=fpr,
                tpr=tpr,
                roc_auc=roc_auc,
            )
            self.results.append((hotkey, model_result))

        return self.results
