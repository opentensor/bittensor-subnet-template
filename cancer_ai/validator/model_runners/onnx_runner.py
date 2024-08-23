from . import BaseRunnerHandler
from typing import List

class OnnxRunnerHandler(BaseRunnerHandler):
    def run(self, X_test: List) -> List:
        import onnxruntime
        import numpy as np

        # Load the ONNX model
        session = onnxruntime.InferenceSession(self.model_path)

        # Stack input images into a single batch
        input_batch = np.stack(X_test)

        # Prepare input for ONNX model
        input_name = session.get_inputs()[0].name
        input_data = {input_name: input_batch}

        # Perform inference on the batch
        results = session.run(None, input_data)[0]

        return results
