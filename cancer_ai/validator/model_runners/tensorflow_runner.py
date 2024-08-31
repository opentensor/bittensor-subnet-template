from . import BaseRunnerHandler
from typing import List


class TensorflowRunnerHandler(BaseRunnerHandler):
    async def run(self, pred_x: List) -> List:
        import tensorflow as tf
        import numpy as np
        from tensorflow.keras.preprocessing.image import load_img
        print("imgs to test", len(pred_x))
        img_list = [load_img(img_path, target_size=(180, 180, 3)) for img_path in pred_x]
        img_list = [np.expand_dims(test_img, axis=0) for test_img in img_list]
        
        model = tf.keras.models.load_model(self.model_path)
        # batched_predictions = model.predict(np.array(img_list))
        # return [batched_predictions[i][0] for i in range(len(img_list))]
        img_list = np.array(img_list)
        img_list = np.squeeze(img_list, axis=1)
        return model.predict(img_list, batch_size=10)
