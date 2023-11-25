from insights.protocol import NETWORK_BITCOIN

BLOCK_HEIGHT_DIFF_WEIGHT = 1
BLOCK_HEIGHT_RECENCY_WEIGHT = 1
CHEAT_FACTOR_WEIGHT = 4
PROCESS_TIME_WEIGHT = 0.2
BLOCKCHAIN_IMPORTANCE_WEIGHT = 0.1

BLOCKCHAIN_IMPORTANCE = {
    'bitcoin': 0.5,
    'ethereum': 0.5
}

def build_miner_distribution(responses):
    miner_distribution = {}
    for response in responses:
        if response is None:
            continue
        network = response.metadata.network
        if network in miner_distribution:
            miner_distribution[network] += 1
        else:
            miner_distribution[network] = 1
    return miner_distribution

def get_dynamic_weight(network, miner_distribution):
    total_miners = sum(miner_distribution.values())
    network_miners = miner_distribution.get(network, 1)
    # Calculate the percentage of miners for this network
    miner_percentage = network_miners / total_miners
    # Adjust weight inversely to the miner percentage
    adjusted_weight = (1 - miner_percentage) * BLOCKCHAIN_IMPORTANCE.get(network, 0.1)
    return adjusted_weight

def calculate_score(network, process_time, start_block_height, last_block_height, blockchain_block_height, miner_distribution, data_samples_are_valid, cheat_factor):
    if not data_samples_are_valid:
        return 0

    blockchain_size_weight = get_dynamic_weight(network, miner_distribution)

    # Process time scoring logic
    if process_time <= 0.1: # 0.1 second
        process_time_score = 1  # Optimal response time
    else:
        # Decrease score based on how much process time exceeds 10ms
        time_penalty = (process_time - 0.1) / (100 - 0.1)
        process_time_score = 1 - time_penalty

    # Block height difference scoring logic
    block_height_diff = abs(last_block_height - blockchain_block_height)
    if block_height_diff > 100:
        block_height_score = -2 * block_height_diff  # Heavy penalty if too far behind
    else:
        block_height_score = -block_height_diff / 100

    # Block height recency scoring logic
    block_height_diff_recency = blockchain_block_height - start_block_height
    if block_height_diff_recency <= 50000:  # Approximately one year of data
        block_height_recency_score = 1 - (block_height_diff_recency / 50000)

    # Calculate total score using weighted average
    total_score = (process_time_score * PROCESS_TIME_WEIGHT +
                   block_height_score * BLOCK_HEIGHT_DIFF_WEIGHT +
                   blockchain_size_weight * BLOCKCHAIN_IMPORTANCE_WEIGHT +
                   block_height_recency_score * BLOCK_HEIGHT_RECENCY_WEIGHT+
                   cheat_factor * CHEAT_FACTOR_WEIGHT)

    # Normalize the score to be within 0 to 1 range
    max_possible_score = PROCESS_TIME_WEIGHT + BLOCK_HEIGHT_DIFF_WEIGHT + BLOCKCHAIN_IMPORTANCE_WEIGHT + BLOCK_HEIGHT_RECENCY_WEIGHT + CHEAT_FACTOR_WEIGHT
    normalized_score = total_score / max_possible_score

    return min(max(normalized_score, 0), 1)


SCORES_FILE = "scores.pt"
import torch
import bittensor as bt

def get_scores_from_file(metagraph):
    try:
        scores = torch.load(SCORES_FILE)
        bt.logging.info(f"Loaded scores from save file: {scores}")
    except Exception as e:
        scores = torch.zeros_like(metagraph.S, dtype=torch.float32)
        bt.logging.info(f"Initialized all scores to 0")
    return scores

def setup_initial_scores(metagraph):
    scores = get_scores_from_file(metagraph)
    scores = scores * (metagraph.total_stake < 1.024e3) # all nodes with more than 1e3 total stake are set to 0 (sets validators weights to 0)
    scores = scores * torch.Tensor([metagraph.neurons[uid].axon_info.ip != '0.0.0.0' for uid in metagraph.uids]) # set all nodes without ips set to 0
    return scores

def verify_data_sample(network, input_result, block_data):
   if network == NETWORK_BITCOIN:
        block_height = int(input_result['block_height'])
        transactions = block_data["tx"]
        num_transactions = len(transactions)
        result = {
            "block_height": block_height,
            "transaction_count": num_transactions,
        }
        is_valid = result["transaction_count"] == input_result["transaction_count"]
        return is_valid
   else:
        return False

