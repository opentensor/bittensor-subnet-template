from . import BaseRunnerHandler
from typing import List

class OnnxRunnerHandler(BaseRunnerHandler):
    def run(self, X_test: List) -> List:
        import onnxruntime
        import numpy as np
        import torch
        from PIL import Image
        from torchvision import transforms

        # Load the ONNX model
        session = onnxruntime.InferenceSession(self.model_path)
        input_name = session.get_inputs()[0].name
    
        results = []
        for img in X_test:
            # Prepare input for ONNX model
            input_data = {input_name: img}
            y_pred = session.run(None, input_data)[0][0]

            # Collect results
            results.append(y_pred[0].tolist())

        return results
