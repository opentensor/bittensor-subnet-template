from . import BaseRunnerHandler
from typing import List

class OnnxRunnerHandler(BaseRunnerHandler):
    def run(self, pred_x: List) -> List:
        import onnxruntime
        import numpy as np
        import torch
        from PIL import Image
        from torchvision import transforms

        # Load the ONNX model
        session = onnxruntime.InferenceSession(self.model_path)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name

        # Preprocess the input
        img_list = [Image.open(img_path) for img_path in pred_x]
        # Define your transformations (resize, normalize, etc.)
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        # preprocess = transforms.Compose([
        #     transforms.Resize(256),
        #     transforms.CenterCrop(224),
        #     transforms.ToTensor(),
        #     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        # ])
        results = []
        for img_path in pred_x:
            # Preprocess the input
            img = Image.open(img_path)
            img = transform(img)
            img = img.unsqueeze(0)  # Add batch dimension

            # Convert to numpy array
            input_data = img.numpy()
            input_data = input_data.astype(np.float32)  # Ensure type is float32

            # Prepare input for ONNX model
            input_data = {input_name: input_data}

            # Run the model
            output = session.run([output_name], input_data)

            # Collect results
            results.append(output[0].tolist())

        return results
