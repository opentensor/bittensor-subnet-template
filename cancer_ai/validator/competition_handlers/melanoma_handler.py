from .base_handler import BaseCompetitionHandler
from .base_handler import ModelEvaluationResult

from PIL import Image
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, roc_curve, auc

class MelanomaCompetitionHandler(BaseCompetitionHandler):
    """
    """
    def __init__(self, path_X_test, y_test) -> None:
        super().__init__(path_X_test, y_test)

    def preprocess_data(self):
        X_test = []
        target_size=(224, 224) #TODO: Change this to the correct size 

        for img_path in self.path_X_test:
            img = Image.open(img_path)
            img = img.resize(target_size)
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.array(img)  
            if img_array.shape[-1] != 3:    # Handle grayscale images
                img_array = np.stack((img_array,) * 3, axis=-1)
            
            img_array = np.transpose(img_array, (2, 0, 1))           # Transpose image to (C, H, W)
            img_array = np.expand_dims(img_array, axis=0)            # Add batch dimension
            X_test.append(img_array)

        X_test = np.array(X_test, dtype=np.float32)

        # Map y_test to 0, 1
        y_test = [1 if y == "True" else 0 for y in self.y_test]

        return X_test, y_test
    
    def evaluate(self, y_test, y_pred, run_time) -> ModelEvaluationResult:
        y_pred_binary = [1 if y > 0.5 else 0 for y in y_pred]
        tested_entries = len(y_test)
        accuracy = accuracy_score(y_test, y_pred_binary)
        precision = precision_score(y_test, y_pred_binary)
        recall = recall_score(y_test, y_pred_binary)
        conf_matrix = confusion_matrix(y_test, y_pred_binary)
        fpr, tpr, _ = roc_curve(y_test, y_pred)
        roc_auc = auc(fpr, tpr)
        return ModelEvaluationResult(
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