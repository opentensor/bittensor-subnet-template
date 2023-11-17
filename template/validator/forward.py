
import torch
import bittensor as bt
from template.utils.uids import get_random_uids
from template.utils.sync import update_scores

from template.protocol import Dummy
from template.validator.reward import get_rewards


async def forward( self ):
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self (:obj:`bittensor.neuron.Neuron`): The neuron object which contains all the necessary state for the validator.

    """
    # TODO(developer): Define how the validator selects a miner to query, how often, etc.
    miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)

    responses = self.dendrite.query(
        # Send the query to miners in the network.
        axons=[self.metagraph.axons[uid] for uid in miner_uids],
        # Construct a dummy query.
        synapse=Dummy(dummy_input=self.step),
        # All responses have the deserialize function called on them before returning.
        deserialize=True,
    )

    # Log the results for monitoring purposes.
    bt.logging.info(f"Received responses: {responses}")

    # TODO(developer): Define how the validator scores responses.
    # Adjust the scores based on responses from miners.
    rewards = get_rewards( self, query = self.step, responses = responses )

    bt.logging.info(f"Scored responses: {rewards}")
    update_scores(self, rewards, miner_uids)
