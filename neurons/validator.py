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
import bittensor as bt
import asyncio
import os
import numpy as np

from cancer_ai.validator.rewarder import WinnersMapping, Rewarder, Score
from cancer_ai.base.base_validator import BaseValidatorNeuron
from cancer_ai.validator.competition_manager import CompetitionManager
from competition_runner import (
    config_for_scheduler,
    run_competitions_tick,
    CompetitionRunLog,
)


class Validator(BaseValidatorNeuron):
    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        self.competition_scheduler = config_for_scheduler(
            self.config, self.hotkeys, test_mode=True
        )
        bt.logging.info(f"Scheduler config: {self.competition_scheduler}")

        self.rewarder = Rewarder(self.winners_mapping)

    async def concurrent_forward(self):
        coroutines = [
            self.competition_loop_tick(self.competition_scheduler),
        ]
        await asyncio.gather(*coroutines)

    async def competition_loop_tick(
        self, scheduler_config: dict[str, CompetitionManager]
    ):

        bt.logging.debug("Run log", self.run_log)
        competition_result = await run_competitions_tick(scheduler_config, self.run_log)

        if not competition_result:
            return

        bt.logging.debug(f"Competition result: {competition_result}")

        winning_evaluation_hotkey, competition_id = competition_result

        # update the scores
        await self.rewarder.update_scores(winning_evaluation_hotkey, competition_id)
        self.winners_mapping = WinnersMapping(
            competition_leader_map=self.rewarder.competition_leader_mapping,
            hotkey_score_map=self.rewarder.scores,
        )
        self.save_state()

        hotkey_to_score_map = self.winners_mapping.hotkey_score_map

        self.scores = [
            np.float32(
                hotkey_to_score_map.get(hotkey, Score(score=0.0, reduction=0.0)).score
            )
            for hotkey in self.metagraph.hotkeys
        ]
        self.save_state()

        await asyncio.sleep(60)

    def save_state(self):
        """Saves the state of the validator to a file."""
        bt.logging.info("Saving validator state.")

        # Save the state of the validator to file.
        if not getattr(self, "winners_mapping", None):
            self.winners_mapping = WinnersMapping(
                competition_leader_map={}, hotkey_score_map={}
            )
        if not getattr(self, "run_log", None):
            self.run_log = CompetitionRunLog(runs=[])

        np.savez(
            self.config.neuron.full_path + "/state.npz",
            scores=self.scores,
            hotkeys=self.hotkeys,
            rewarder_config=self.winners_mapping.model_dump(),
            run_log=self.run_log.model_dump(),
        )

    def load_state(self):
        """Loads the state of the validator from a file."""
        bt.logging.info("Loading validator state.")

        if not os.path.exists(self.config.neuron.full_path + "/state.npz"):
            bt.logging.info("No state file found. Creating the file.")
            np.savez(
                self.config.neuron.full_path + "/state.npz",
                scores=self.scores,
                hotkeys=self.hotkeys,
                rewarder_config=self.winners_mapping.model_dump(),
                run_log=self.run_log.model_dump(),
            )
            return

        # Load the state of the validator from file.
        state = np.load(self.config.neuron.full_path + "/state.npz", allow_pickle=True)
        self.scores = state["scores"]
        self.hotkeys = state["hotkeys"]
        self.winners_mapping = WinnersMapping.model_validate(
            state["rewarder_config"].item()
        )
        self.run_log = CompetitionRunLog.model_validate(state["run_log"].item())


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            # bt.logging.info(f"Validator running... {time.time()}")
            time.sleep(5)
