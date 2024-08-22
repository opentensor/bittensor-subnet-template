from . import BaseRunnerHandler
from typing import List
from ..utils import log_time


class ONNXRunnerHandler(BaseRunnerHandler):
    @log_time
    async def run(self, pred_x: List) -> List:
        # example, might not work
        import random

        output = [random.randrange(0, 1) for _ in range(len(pred_x))]
        return output
