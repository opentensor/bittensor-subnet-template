from . import BaseRunnerHandler
from typing import List, AsyncGenerator
import numpy as np


class OnnxRunnerHandler(BaseRunnerHandler):
    async def get_chunk_of_data(
        self, X_test: List, chunk_size: int
    ) -> AsyncGenerator[List]:
        """Opens images using PIL and yields a chunk of them"""
        import PIL.Image as Image

        for i in range(0, len(X_test), chunk_size):
            print(f"Processing chunk {i} to {i + chunk_size}")
            chunk = []
            for img_path in X_test[i : i + chunk_size]:
                img = Image.open(img_path)
                chunk.append(img)
            chunk = self.preprocess_data(chunk)
            yield chunk

    def preprocess_data(self, X_test: List) -> List:
        new_X_test = []
        target_size = (224, 224)  # TODO: Change this to the correct size

        for img in X_test:
            img = img.resize(target_size)
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.array(img)
            if img_array.shape[-1] != 3:  # Handle grayscale images
                img_array = np.stack((img_array,) * 3, axis=-1)

            img_array = np.transpose(
                img_array, (2, 0, 1)
            )  # Transpose image to (C, H, W)

            new_X_test.append(img_array)

        new_X_test = np.array(new_X_test, dtype=np.float32)

        return new_X_test

    async def run(self, X_test: List) -> List:
        import onnxruntime

        session = onnxruntime.InferenceSession(self.model_path)

        results = []

        async for chunk in self.get_chunk_of_data(X_test, chunk_size=200):
            input_batch = np.stack(chunk, axis=0)
            input_name = session.get_inputs()[0].name
            input_data = {input_name: input_batch}

            chunk_results = session.run(None, input_data)[0]
            results.extend(chunk_results)

        return results
