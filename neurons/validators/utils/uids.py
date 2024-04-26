import torch
import random
import bittensor as bt
from typing import List


def check_uid_availability(
    metagraph: "bt.metagraph.Metagraph", uid: int, vpermit_tao_limit: int
) -> bool:
    """Check if uid is available. The UID should be available if it is serving and has less than vpermit_tao_limit stake
    Args:
        metagraph (:obj: bt.metagraph.Metagraph): Metagraph object
        uid (int): uid to be checked
        vpermit_tao_limit (int): Validator permit tao limit
    Returns:
        bool: True if uid is available, False otherwise
    """
    # Filter non serving axons.
    if not metagraph.axons[uid].is_serving:
        return False
    if metagraph.validator_permit[uid]:  
        if metagraph.S[uid] >= vpermit_tao_limit:
            return False
        
        # Filter out uid without IP.
        if metagraph.neurons[uid].axon_info.ip == '0.0.0.0':
            return False
    # Available otherwise.
    return True

def get_top_miner_uids(
    metagraph: "bt.metagraph.Metagraph", top_rate: float = 1, exclude: List[int] = None, vpermit_tao_limit: int = 4096
) -> torch.LongTensor:
    """Returns the available top miner UID from the metagraph.
    Args:
        metagraph (bt.metagraph.Metagraph): Metagraph object
        vpermit_tao_limit (int): Validator permit tao limit
        exclude (List[int]): List of uids to exclude from the random sampling.
    Returns:
        top_miner_uid (torch.LongTensor): The top miner UID.
    """
    candidate_uids = []
    for uid in range(metagraph.n.item()):
        uid_is_available = check_uid_availability(
            metagraph, uid, vpermit_tao_limit
        )
        uid_is_not_excluded = exclude is None or uid not in exclude

        if uid_is_available:
            if uid_is_not_excluded:
                candidate_uids.append(uid)
    # Consider both of incentive and trust score
    values = [(uid, metagraph.I[uid] * metagraph.trust[uid]) for uid in candidate_uids]
    top_rate_num_items = max(1, int(top_rate * len(candidate_uids)))
    # Consider only incentive
    # values = [(uid, metagraph.I[uid]) for uid in candidate_uids] 
    
    sorted_values = sorted(values,key=lambda x: x[1], reverse=True)
    top_miner_uids = torch.tensor([uid for uid, _ in sorted_values[:top_rate_num_items]])
    return top_miner_uids    
    
    

def get_random_uids(
    self, k: int, exclude: List[int] = None
) -> torch.LongTensor:
    """Returns k available random uids from the metagraph.
    Args:
        k (int): Number of uids to return.
        exclude (List[int]): List of uids to exclude from the random sampling.
    Returns:
        uids (torch.LongTensor): Randomly sampled available uids.
    Notes:
        If `k` is larger than the number of available `uids`, set `k` to the number of available `uids`.
    """
    candidate_uids = []
    for uid in range(self.metagraph.n.item()):
        uid_is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        uid_is_not_excluded = exclude is None or uid not in exclude

        if uid_is_available:
            if uid_is_not_excluded:
                candidate_uids.append(uid)

    k = max(1, min(len(candidate_uids), k))
    uids = torch.tensor(random.sample(candidate_uids, k))
    return uids

def get_uids_batch(self, batch_size: int, exclude: List[int] = None):
    candidate_uids = []
    for uid in range(self.metagraph.n.item()):
        uid_is_available = check_uid_availability(
            self.metagraph, uid, self.config.neuron.vpermit_tao_limit
        )
        uid_is_not_excluded = exclude is None or uid not in exclude and uid != self.uid

        if uid_is_available:
            if uid_is_not_excluded:
                candidate_uids.append(uid)

    # Shuffle the list of available uids
    random.shuffle(candidate_uids)
    batch_size = max(1, min(len(candidate_uids), batch_size))

    # Yield batches of uids
    for i in range(0, len(candidate_uids), batch_size):
        yield torch.tensor(candidate_uids[i:i+batch_size])
