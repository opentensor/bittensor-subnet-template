from . import BaseRunnerHandler
from typing import List


class PytorchRunnerHandler(BaseRunnerHandler):
    async def run(self, pred_x: List) -> List:
        # example, might not work
        from torch import load

        model = load(self.model_path)
        model.eval()
        output = model(pred_x)
        return output
