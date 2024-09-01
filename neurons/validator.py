# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import time
from typing import Any, List
import bittensor as bt
import asyncio

from numpy import ndarray

from cancer_ai.base.validator import BaseValidatorNeuron
from cancer_ai.validator import forward
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
from cancer_ai.validator.competition_manager import CompetitionManager
from cancer_ai.validator.competition_handlers.base_handler import ModelEvaluationResult
from .competition_runner import competition_loop, config_for_scheduler, run_competitions_tick
from .rewarder import RewarderConfig, Rewarder, Score


class Validator(BaseValidatorNeuron):
    """
    Your validator neuron class. You should use this class to define your validator's behavior. In particular, you should replace the forward function with your own logic.

    This class inherits from the BaseValidatorNeuron class, which in turn inherits from BaseNeuron. The BaseNeuron class takes care of routine tasks such as setting up wallet, subtensor, metagraph, logging directory, parsing config, etc. You can override any of the methods in BaseNeuron if you need to customize the behavior.

    This class provides reasonable default behavior for a validator such as keeping a moving average of the scores of the miners and using them to set weights at the end of each epoch. Additionally, the scores are reset for new hotkeys at the end of each epoch.
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        self.rewarder_config = RewarderConfig({},{})
        self.load_state()
        self.scheduler_config = config_for_scheduler(self.config, self.hotkeys)

        self.rewarder = Rewarder(self.rewarder_config)
        
        asyncio.run_coroutine_threadsafe(competition_loop(self.scheduler_config, self.rewarder_config), self.loop)

    async def competition_loop(self, scheduler_config: dict[str, CompetitionManager], rewarder_config: RewarderConfig):
        """Example of scheduling coroutine"""
        while True:
            competition_result = await run_competitions_tick(scheduler_config)
            bt.logging.debug(f"Competition result: {competition_result}")
            if competition_result:
                winning_evaluation_hotkey, competition_id = competition_result

                # update the scores
                await self.rewarder.update_scores(winning_evaluation_hotkey, competition_id)
                self.rewarder_config = RewarderConfig(self.rewarder.competition_leader_mapping, self.rewarder.scores)
                self.save_state()

                hotkey_to_score_map = self.rewarder_config.hotkey_to_score_map

                self.scores = [
                    hotkey_to_score_map.get(hotkey, Score(score=0.0, reduction=0.0)).score 
                    for hotkey in self.metagraph.hotkeys
                ]
                self.save_state()
                print(".....................Updated rewarder config:")
                print(self.rewarder_config)
            await asyncio.sleep(60)

# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info(f"Validator running... {time.time()}")
            time.sleep(5)
