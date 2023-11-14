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
import torch
import copy
import bittensor as bt
import neurons.base.validator as validator

# TODO: Replace spec version with your own implementation
import template
spec_version = template.__spec_version__

def check_registered( self ):
    # Step 5: Connect the validator to the network
    if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
        bt.logging.error(
            f"\nYour validator: {self.wallet} if not registered to chain connection: {self.subtensor} \nRun btcli register and try again."
        )
        exit()


def sync( self ):

    check_registered( self )

    if should_sync_metagraph( self ):
        resync_metagraph( self )

    # TODO: If miners are going to use this funciton we need to define the behaviour of weight setting
    if should_set_weights( self ):
        set_weights( self )

    # if should_save_state( self ):
    #     save_state( self )


def should_sync_metagraph(self):
    # Check if enough epoch blocks have elapsed since the last checkpoint.
    # Note: Steffen removed check for config.disable_set_weights
    return (
        (self.block - self.metagraph.last_update[self.uid]) > self.config.neuron.epoch_length
    )


def resync_metagraph(self: "validator"):
    """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
    bt.logging.info("resync_metagraph()")

    # Copies state of metagraph before syncing.
    previous_metagraph = copy.deepcopy(self.metagraph)

    # Sync the metagraph.
    self.metagraph.sync(subtensor=self.subtensor)

    # Check if the metagraph axon info has changed.
    metagraph_axon_info_updated = previous_metagraph.axons != self.metagraph.axons

    if metagraph_axon_info_updated:
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


def set_weights(self):
    # Calculate the average reward for each uid across non-zero values.
    # Replace any NaN values with 0.
    raw_weights = torch.nn.functional.normalize(self.moving_averaged_scores, p=1, dim=0)
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


def update_scores(self, rewards, uids):

    # Compute forward pass rewards, assumes uids are mutually exclusive.
    # shape: [ metagraph.n ]
    scattered_rewards: torch.FloatTensor = self.scores.scatter(
        0, torch.tensor(uids).to(self.device), rewards
    ).to(self.device)
    bt.logging.debug(f"Scattered rewards: {rewards}")

    # Update moving_averaged_scores with rewards produced by this step.
    # shape: [ metagraph.n ]
    alpha: float = self.config.neuron.moving_average_alpha
    self.scores: torch.FloatTensor = alpha * scattered_rewards + (
        1 - alpha
    ) * self.scores.to(self.device)
    bt.logging.debug(f"Updated moving avg scores: {self.moving_averaged_scores}")
