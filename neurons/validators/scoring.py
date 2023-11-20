# Constants for blockchain importance
BLOCKCHAIN_IMPORTANCE = {
    'bitcoin': 0.4,
    'ethereum': 0.4,
    'ltc': 0.05,
    'doge': 0.15
}

# Example miner distribution (should be dynamically calculated)
MINER_DISTRIBUTION = {
    'bitcoin': 1,  # Number of miners
    'ltc': 100,
    'doge': 100
}

def get_dynamic_weight(network):
    total_miners = sum(MINER_DISTRIBUTION.values())
    network_miners = MINER_DISTRIBUTION.get(network, 1)
    # Calculate the percentage of miners for this network
    miner_percentage = network_miners / total_miners
    # Adjust weight inversely to the miner percentage
    adjusted_weight = (1 - miner_percentage) * BLOCKCHAIN_IMPORTANCE.get(network, 0.1)
    return adjusted_weight

# Constants for weightings
PROCESS_TIME_WEIGHT = 0.2
BLOCK_HEIGHT_DIFF_WEIGHT = 1
BLOCKCHAIN_IMPORTANCE_WEIGHT = 0.66  # Lower weight for blockchain importance

# Scoring function
def calculate_score(response, last_block_height, network):
    if response is None or not response.data_sample_is_valid:
        return 0  # Return 0 if response is None or data is not correct

    blockchain_size_weight = get_dynamic_weight(network)

    # Initialize score components
    process_time_score = block_height_score = 0

    if response.dendrite:
        process_time = response.dendrite.process_time
        # Process time scoring logic
        if process_time <= 10:
            process_time_score = 1  # Optimal response time
        else:
            # Decrease score based on how much process time exceeds 10ms
            time_penalty = (process_time - 10) / (10000 - 10)
            process_time_score = 1 - time_penalty

    if response:
        data_sample_block_height = response.block_height
        # Block height difference scoring logic
        block_height_diff = abs(last_block_height - data_sample_block_height)
        if block_height_diff > 100:
            block_height_score = -2 * block_height_diff  # Heavy penalty if too far behind
        else:
            block_height_score = -block_height_diff / 100

    # Calculate total score using weighted average
    total_score = (process_time_score * PROCESS_TIME_WEIGHT +
                   block_height_score * BLOCK_HEIGHT_DIFF_WEIGHT +
                   blockchain_size_weight * BLOCKCHAIN_IMPORTANCE_WEIGHT)

    # Normalize the score to be within 0 to 1 range
    max_possible_score = PROCESS_TIME_WEIGHT + BLOCKCHAIN_IMPORTANCE_WEIGHT
    normalized_score = total_score / max_possible_score

    return min(max(normalized_score, 0), 1)
