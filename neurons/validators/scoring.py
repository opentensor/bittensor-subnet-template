
# this could got to ENV variable like BLOCKCHAIN_IMPORTANCE_BITCOIN = 0.4 OR maybe a config file?

BLOCKCHAIN_IMPORTANCE = {
    'bitcoin': 0.4,
    'ethereum': 0.4,
    'ltc': 0.05,
    'doge': 0.15
}

def build_miner_distribution(responses):
    """
    Build a dictionary representing the distribution of miners across different networks.

    :param responses: List of response objects.
    :return: Dictionary with network names as keys and the count of miners as values.
    """
    miner_distribution = {}

    for response in responses:
        if response is None:
            continue

        # Extracting network information from the response
        network = response.metadata.network
        # You can add more data extractions here if necessary

        # Update the miner count for the network
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

# Constants for weightings
PROCESS_TIME_WEIGHT = 0.2
BLOCK_HEIGHT_DIFF_WEIGHT = 1
BLOCKCHAIN_IMPORTANCE_WEIGHT = 0.66  # Lower weight for blockchain importance

# Scoring function
def calculate_score(response, last_block_height, network, miner_distribution, data_sample_is_valid):
    if data_sample_is_valid:
        return 0

    blockchain_size_weight = get_dynamic_weight(network, miner_distribution)

    # Initialize score components
    process_time_score = block_height_score = 0

    if response.dendrite:
        process_time = response.dendrite.process_time
        # Process time scoring logic
        if process_time <= 0.1: # 0.1 second
            process_time_score = 1  # Optimal response time
        else:
            # Decrease score based on how much process time exceeds 10ms
            time_penalty = (process_time - 0.1) / (100 - 0.1)
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
