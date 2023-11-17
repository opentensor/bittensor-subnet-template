# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Opentensor Foundation

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

# Utils for checkpointing and saving the model.
import copy
import torch
import bittensor as bt
from typing import List

import template

spec_version = template.__spec_version__


def check_registered( self ):
    if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
        bt.logging.error(
            f"\nYour validator: {self.wallet} if not registered to chain connection: {self.subtensor} \nRun btcli register and try again."
        )
        exit()


def sync( self ):
    """
    Wrapper for synchronizing the state of the network for the given miner or validator.
    """

    check_registered( self )

    if should_sync_metagraph( self ):
        resync_metagraph( self )

    if should_set_weights( self ):
        set_weights( self )

    save_state( self )


def set_weights(self):
    """
    Sets the validator or miner's weights on the Bittensor network.

    For miners:
    This function assigns a weight of 1 to the current miner (identified by its UID) and
    a weight of 0 to all other peers in the network. The weights determine the trust level
    the miner assigns to other nodes on the network.

    For validators:
    This function assigns weights to the metagraph hotkeys based on the scores it has
    received from the miners. The weights determine the trust and incentive level the 
    validator assigns to miner nodes on the network.

    Raises:
        Exception: If there's an error while setting weights, the exception is logged for diagnosis.
    """
    if issubclass(type(self), template.base.BaseValidatorNeuron):

        # Calculate the average reward for each uid across non-zero values.
        # Replace any NaN values with 0.
        raw_weights = torch.nn.functional.normalize(self.scores, p=1, dim=0)
        bt.logging.trace("raw_weights", raw_weights)
        bt.logging.trace("top10 values", raw_weights.sort()[0])
        bt.logging.trace("top10 uids", raw_weights.sort()[1])

        # Process the raw weights to final_weights via subtensor limitations.
        (
            processed_weight_uids,
            processed_weights,
        ) = bt.utils.weight_utils.process_weights_for_netuid(
            uids=self.metagraph.uids.to("cpu"),
            weights=raw_weights.to("cpu"),
            netuid=self.config.netuid,
            subtensor=self.subtensor,
            metagraph=self.metagraph,
        )
        bt.logging.trace("processed_weights", processed_weights)
        bt.logging.trace("processed_weight_uids", processed_weight_uids)

        # Set the weights on chain via our subtensor connection.
        self.subtensor.set_weights(
            wallet=self.wallet,
            netuid=self.config.netuid,
            uids=processed_weight_uids,
            weights=processed_weights,
            wait_for_finalization=False,
            version_key=spec_version,
        )

    elif issubclass(type(self), template.base.BaseMinerNeuron):

        try:
            # --- query the chain for the most current number of peers on the network
            chain_weights = torch.zeros(subtensor.subnetwork_n(netuid=self.metagraph.netuid))
            chain_weights[uid] = 1

            # --- Set weights.
            self.subtensor.set_weights(
                uids=torch.arange(0, len(chain_weights)),
                netuid=self.metagraph.netuid,
                weights=chain_weights,
                wait_for_inclusion=False,
                wallet=self.wallet,
                version_key=spec_version,
            )
        except Exception as e:
            bt.logging.error(f"Failed to set weights on chain with exception: { e }")

    else:
        raise Exception("Neuron must be either a subclass of BaseValidatorNeuron or BaseMinerNeuron.")


def should_sync_metagraph(self):
    # Check if enough epoch blocks have elapsed since the last checkpoint.
    return (
        (self.block - self.metagraph.last_update[self.uid]) > self.config.neuron.epoch_length
    )


def resync_metagraph(self):
    """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
    bt.logging.info("resync_metagraph()")

    # Copies state of metagraph before syncing.
    previous_metagraph = copy.deepcopy(self.metagraph)

    # Sync the metagraph.
    self.metagraph.sync(subtensor=self.subtensor)

    # Check if the metagraph axon info has changed.
    if (
        issubclass(type(self), template.base.BaseValidatorNeuron) and
        previous_metagraph.axons != self.metagraph.axons
    ):
        bt.logging.info(
            "Metagraph updated, re-syncing hotkeys, dendrite pool and moving averages"
        )
        # Zero out all hotkeys that have been replaced.
        for uid, hotkey in enumerate(self.hotkeys):
            if hotkey != self.metagraph.hotkeys[uid]:
                self.scores[uid] = 0  # hotkey has been replaced

        # Check to see if the metagraph has changed size.
        # If so, we need to add new hotkeys and moving averages.
        if len(self.hotkeys) < len(self.metagraph.hotkeys):
            # Update the size of the moving average scores.
            new_moving_average = torch.zeros((self.metagraph.n)).to(self.device)
            min_len = min(len(self.hotkeys), len(self.scores))
            new_moving_average[:min_len] = self.scores[:min_len]
            self.scores = new_moving_average

        # Update the hotkeys.
        self.hotkeys = copy.deepcopy(self.metagraph.hotkeys)


def should_set_weights(self) -> bool:
    # Check if enough epoch blocks have elapsed since the last epoch.
    if self.config.neuron.disable_set_weights:
        return False

    return (
        (self.block - self.metagraph.last_update[self.uid]) > self.config.neuron.epoch_length
    )


def update_scores(self, rewards: torch.FloatTensor, uids: List[int]):

    # Check if rewards contains NaN values.
    if torch.isnan(rewards).any():
        bt.logging.warning(f"NaN values detected in rewards: {rewards}")
        # Replace any NaN values in rewards with 0.
        rewards = torch.nan_to_num(rewards, 0)

    # Compute forward pass rewards, assumes uids are mutually exclusive.
    # shape: [ metagraph.n ]
    scattered_rewards: torch.FloatTensor = self.scores.scatter(
        0, torch.tensor(uids).to(self.device), rewards
    ).to(self.device)
    bt.logging.debug(f"Scattered rewards: {rewards}")

    # Update scores with rewards produced by this step.
    # shape: [ metagraph.n ]
    alpha: float = self.config.neuron.moving_average_alpha
    self.scores: torch.FloatTensor = alpha * scattered_rewards + (
        1 - alpha
    ) * self.scores.to(self.device)
    bt.logging.debug(f"Updated moving avg scores: {self.scores}")



def save_state(self):
    r"""
    Save hotkeys, neuron weights and moving average scores to filesystem.
    
    Typically, only validators would need this functionality.
    """

    if issubclass(type(self), template.base.BaseMinerNeuron):
        return

    bt.logging.info("save_state()")
    try:
        neuron_state_dict = {
            "neuron_weights": self.scores.to("cpu").tolist(),
            "neuron_hotkeys": self.hotkeys,
        }
        torch.save(neuron_state_dict, f"{self.config.neuron.full_path}/model.torch")
        bt.logging.success(
            prefix="Saved model",
            sufix=f"<blue>{ self.config.neuron.full_path }/model.torch</blue>",
        )
    except Exception as e:
        bt.logging.warning(f"Failed to save model with error: {e}")
