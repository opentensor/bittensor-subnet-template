from . import BaseRunnerHandler
from typing import List


class TensorflowRunnerHandler(BaseRunnerHandler):
    async def run(self, pred_x: List) -> List:
        return []
