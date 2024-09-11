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
import asyncio
import os
import traceback
import json

import bittensor as bt
import numpy as np
import wandb

from cancer_ai.chain_models_store import ChainModelMetadata, ChainMinerModelStore
from cancer_ai.validator.rewarder import CompetitionWinnersStore, Rewarder, Score
from cancer_ai.base.base_validator import BaseValidatorNeuron
from cancer_ai.validator.competition_manager import CompetitionManager
from competition_runner import (
    get_competitions_schedule,
    run_competitions_tick,
    CompetitionRunStore,
)

RUN_EVERY_N_MINUTES = 15  # TODO move to config
BLACKLIST_FILE_PATH = "config/hotkey_blacklist.json"
BLACKLIST_FILE_PATH_TESTNET = "config/hotkey_blacklist_testnet.json"


class Validator(BaseValidatorNeuron):
    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)
        self.hotkey = self.wallet.hotkey.ss58_address
        self.competition_scheduler = get_competitions_schedule(
            bt_config = self.config,
            subtensor = self.subtensor,
            chain_models_store = self.chain_models_store,
            hotkeys = self.hotkeys,
            validator_hotkey = self.hotkey,
            test_mode = False,
        )
        bt.logging.info(f"Scheduler config: {self.competition_scheduler}")

        self.rewarder = Rewarder(self.winners_store)
        self.chain_models = ChainModelMetadata(
            self.subtensor, self.config.netuid, self.wallet
        )

    async def concurrent_forward(self):
        coroutines = [
            self.refresh_miners(),
            self.competition_loop_tick(),
        ]
        await asyncio.gather(*coroutines)

    async def refresh_miners(self):
        """
        downloads miner's models  from the chain and updates the local store
        """

        if self.chain_models_store.last_updated is not None and (
            time.time() - self.chain_models_store.last_updated
            < RUN_EVERY_N_MINUTES * 60
        ):
            bt.logging.debug("Skipping model refresh, not enough time passed")
            return

        bt.logging.info("Synchronizing miners from the chain")
        bt.logging.info(f"Amount of hotkeys: {len(self.hotkeys)}")

        blacklist_file = (
            BLACKLIST_FILE_PATH_TESTNET
            if self.config.test_mode
            else BLACKLIST_FILE_PATH
        )

        with open(blacklist_file, "r") as f:
            BLACKLISTED_HOTKEYS = json.load(f)

        for hotkey in self.hotkeys:
            if hotkey in BLACKLISTED_HOTKEYS:
                bt.logging.debug(f"Skipping blacklisted hotkey {hotkey}")
                continue

        new_chain_miner_store = ChainMinerModelStore(hotkeys={})
        for hotkey in self.hotkeys:
            hotkey = str(hotkey)

            # TODO add test mode for syncing just once. Then you have to delete state.npz file to sync again
            # if hotkey in self.chain_models_store.hotkeys:
            #     bt.logging.debug(f"Skipping hotkey {hotkey}, already added")
            #     continue

            hotkey_metadata = await self.chain_models.retrieve_model_metadata(hotkey)
            if not hotkey_metadata:
                bt.logging.warning(
                    f"Cannot get miner model for hotkey {hotkey} from the chain, skipping"
                )
            new_chain_miner_store.hotkeys[hotkey] = hotkey_metadata

        self.chain_models_store = new_chain_miner_store
        hotkeys_with_models = [
            hotkey
            for hotkey in self.chain_models_store.hotkeys
            if self.chain_models_store.hotkeys[hotkey]
        ]

        bt.logging.info(
            f"Amount of miners: {len(self.chain_models_store.hotkeys)},  with models: {len(hotkeys_with_models)}"
        )
        self.chain_models_store.last_updated = time.time()
        self.save_state()

    async def competition_loop_tick(self):
        """Main competition loop tick."""

        # for testing purposes
        # self.run_log = CompetitionRunStore(runs=[])

        self.competition_scheduler = get_competitions_schedule(
            bt_config = self.config,
            subtensor = self.subtensor,
            chain_models_store = self.chain_models_store,
            hotkeys = self.hotkeys,
            validator_hotkey = self.hotkey,
            test_mode = False,
        )
        try:
            winning_hotkey, competition_id, winning_model_result = (
                await run_competitions_tick(self.competition_scheduler, self.run_log)
            )
        except Exception:
            formatted_traceback = traceback.format_exc()
            bt.logging.error(f"Error running competition: {formatted_traceback}")
            wandb.init(
                reinit=True, project="competition_id", group="competition_evaluation"
            )
            wandb.log(
                {
                    "winning_evaluation_hotkey": "",
                    "run_time": "",
                    "validator_hotkey": self.wallet.hotkey.ss58_address,
                    "errors": str(formatted_traceback),
                }
            )
            wandb.finish()
            return

        if not winning_hotkey:
            return

        wandb.init(project=competition_id, group="competition_evaluation")
        run_time_s = (
            self.run_log.runs[-1].end_time - self.run_log.runs[-1].start_time
        ).seconds
        wandb.log(
            {
                "winning_hotkey": winning_hotkey,
                "run_time_s": run_time_s,
                "validator_hotkey": self.wallet.hotkey.ss58_address,
                "errors": "",
            }
        )
        wandb.finish()

        bt.logging.info(f"Competition result for {competition_id}: {winning_hotkey}")

        # update the scores
        await self.rewarder.update_scores(
            winning_hotkey, competition_id, winning_model_result
        )
        self.winners_store = CompetitionWinnersStore(
            competition_leader_map=self.rewarder.competition_leader_mapping,
            hotkey_score_map=self.rewarder.scores,
        )
        self.save_state()

        self.scores = [
            np.float32(
                self.winners_store.hotkey_score_map.get(
                    hotkey, Score(score=0.0, reduction=0.0)
                ).score
            )
            for hotkey in self.metagraph.hotkeys
        ]
        self.save_state()

    def save_state(self):
        """Saves the state of the validator to a file."""
        bt.logging.debug("Saving validator state.")

        # Save the state of the validator to file.
        if not getattr(self, "winners_store", None):
            self.winners_store = CompetitionWinnersStore(
                competition_leader_map={}, hotkey_score_map={}
            )
            bt.logging.debug("Winner store empty, creating new one")
        if not getattr(self, "run_log", None):
            self.run_log = CompetitionRunStore(runs=[])
            bt.logging.debug("Competition run store empty, creating new one")
        if not getattr(self, "chain_models_store", None):
            self.chain_models_store = ChainMinerModelStore(hotkeys={})
            bt.logging.debug("Chain model store empty, creating new one")

        np.savez(
            self.config.neuron.full_path + "/state.npz",
            scores=self.scores,
            hotkeys=self.hotkeys,
            winners_store=self.winners_store.model_dump(),
            run_log=self.run_log.model_dump(),
            chain_models_store=self.chain_models_store.model_dump(),
        )

    def create_empty_state(self):
        bt.logging.info("Creating empty state file.")
        np.savez(
            self.config.neuron.full_path + "/state.npz",
            scores=self.scores,
            hotkeys=self.hotkeys,
            winners_store=self.winners_store.model_dump(),
            run_log=self.run_log.model_dump(),
            chain_models_store=self.chain_models_store.model_dump(),
        )
        return

    def load_state(self):
        """Loads the state of the validator from a file."""
        bt.logging.info("Loading validator state.")

        if not os.path.exists(self.config.neuron.full_path + "/state.npz"):
            bt.logging.info("No state file found.")
            self.create_empty_state()

        try:
            # Load the state of the validator from file.
            state = np.load(
                self.config.neuron.full_path + "/state.npz", allow_pickle=True
            )
            bt.logging.trace(state["chain_models_store"])
            self.scores = state["scores"]
            self.hotkeys = state["hotkeys"]
            self.winners_store = CompetitionWinnersStore.model_validate(
                state["winners_store"].item()
            )
            self.run_log = CompetitionRunStore.model_validate(state["run_log"].item())
            bt.logging.debug(state["chain_models_store"].item())
            self.chain_models_store = ChainMinerModelStore.model_validate(
                state["chain_models_store"].item()
            )
        except Exception as e:
            bt.logging.error(f"Error loading state: {e}")
            self.create_empty_state()


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            # bt.logging.info(f"Validator running... {time.time()}")
            time.sleep(5)
