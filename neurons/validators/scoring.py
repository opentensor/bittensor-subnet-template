from insights.protocol import NETWORK_BITCOIN
import bittensor as bt

CHEAT_FACTOR_WEIGHT = 3
BLOCK_HEIGHT_DIFF_WEIGHT = 1.5
BLOCK_HEIGHT_RECENCY_WEIGHT = 1.5
PROCESS_TIME_WEIGHT = 0.5
BLOCKCHAIN_IMPORTANCE_WEIGHT = 0.2

BLOCKCHAIN_IMPORTANCE = {
    'bitcoin': 0.5,
    'ethereum': 0.5
}

def get_dynamic_weight(network, miner_distribution):
    # Ensure miner_distribution is not empty and contains valid data
    if not miner_distribution or not isinstance(miner_distribution, dict):
        raise ValueError("Invalid miner distribution data")

    total_miners = sum(miner_distribution.values())

    # Check to avoid division by zero if total_miners is zero
    if total_miners == 0:
        raise ValueError("Total number of miners is zero, cannot compute weight")

    network_miners = miner_distribution.get(network, 0)
    # Calculate the percentage of miners for this network
    miner_percentage = network_miners / total_miners if total_miners else 0

    # Adjust weight inversely to the miner percentage
    adjusted_weight = (1 - miner_percentage) * BLOCKCHAIN_IMPORTANCE.get(network, 0.1)

    # Ensure the adjusted weight is non-negative
    return max(0, adjusted_weight)


def calculate_score(network, process_time, start_block_height, last_block_height, blockchain_block_height, miner_distribution, data_samples_are_valid, cheat_factor):
    # Initial logging for debugging purposes
    bt.logging.info(f"Calculating score for network: {network}, process_time: {process_time}, start_block_height: {start_block_height}, last_block_height: {last_block_height}, blockchain_block_height: {blockchain_block_height}, miner_distribution: {miner_distribution}, data_samples_are_valid: {data_samples_are_valid}, cheat_factor: {cheat_factor}")

    # Return a score of 0 if the data samples are not valid
    if not data_samples_are_valid:
        return 0

    # Calculate dynamic weight based on network and miner distribution
    blockchain_size_weight = get_dynamic_weight(network, miner_distribution)
    bt.logging.debug(f"Blockchain size weight: {blockchain_size_weight}")

    # Process time scoring logic: Higher score for lower process time
    process_time_score = max(0, min(1, 2 - 10 * process_time))  # Ensuring the score is between 0 and 1
    bt.logging.debug(f"Process time score: {process_time_score}")

    # Block height difference scoring logic: Lower score for higher block height difference
    block_height_diff = abs(last_block_height - blockchain_block_height)
    block_height_score = max(0, min(1, 1 - block_height_diff / 100))  # Normalizing score to be between 0 and 1
    bt.logging.debug(f"Block height score: {block_height_score}")

    # Block height recency scoring logic: Higher score for more recent data
    block_height_diff_recency = blockchain_block_height - start_block_height
    block_height_recency_score = max(0, min(1, 1 - block_height_diff_recency / 50000))  # Normalizing score to be between 0 and 1
    bt.logging.debug(f"Block height recency score: {block_height_recency_score}")

    # Calculate total score using weighted average
    total_score = (process_time_score * PROCESS_TIME_WEIGHT +
                   block_height_score * BLOCK_HEIGHT_DIFF_WEIGHT +
                   blockchain_size_weight * BLOCKCHAIN_IMPORTANCE_WEIGHT +
                   block_height_recency_score * BLOCK_HEIGHT_RECENCY_WEIGHT +
                   max(0, 1 - cheat_factor) * CHEAT_FACTOR_WEIGHT)  # Ensuring cheat factor reduces the score
    bt.logging.debug(f"Total score: {total_score}")

    # Normalize the score to be within 0 to 1 range
    max_possible_score = PROCESS_TIME_WEIGHT + BLOCK_HEIGHT_DIFF_WEIGHT + BLOCKCHAIN_IMPORTANCE_WEIGHT + BLOCK_HEIGHT_RECENCY_WEIGHT + CHEAT_FACTOR_WEIGHT
    normalized_score = total_score / max_possible_score
    normalized_score = min(max(normalized_score, 0), 1)  # Ensuring the score is within 0 to 1
    bt.logging.info(f"Final normalized score: {normalized_score}")

    return normalized_score

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

