
import torch
import bittensor as bt
from utils.uids import get_random_uids
from utils.sync import update_scores

import template
from template.reward import get_rewards

def forward( self ):
    # TODO(developer): Define how the validator selects a miner to query, how often, etc.

    miner_uids = get_random_uids( self )

    responses = self.dendrite.query(
        # Send the query to miners in the network.
        miner_uids,
        # Construct a dummy query.
        template.protocol.Dummy(dummy_input=self.step),  # Construct a dummy query.
        # All responses have the deserialize function called on them before returning.
        deserialize=True,
    )


    # Log the results for monitoring purposes.
    bt.logging.info(f"Received responses: {responses}")

    # TODO(developer): Define how the validator scores responses.
    # Adjust the scores based on responses from miners.
    rewards = get_rewards( self, responses )

    bt.logging.info(f"Scored responses: {rewards}")
    update_scores(self, rewards, miner_uids)
