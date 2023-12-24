import bittensor as bt
from neurons.remote_config import ValidatorConfig
from neurons.validators.miner_registry import MinerRegistryManager

class Scorer:
    def __init__(self, config: ValidatorConfig, miner_registry_manager: MinerRegistryManager):
        self.config = config
        self.miner_registry_manager = miner_registry_manager


    def get_dynamic_weight(self, network, miner_distribution):
        total_miners = sum(miner_distribution.values())

        # Check to avoid division by zero if total_miners is zero
        if total_miners == 0:
            return 0.01

        network_miners = miner_distribution.get(network, 0)
        # Calculate the percentage of miners for this network
        miner_percentage = network_miners / total_miners if total_miners else 0

        # Adjust weight inversely to the miner percentage
        blockchain_importance = self.config.get_network_importance('bitcoin')
        adjusted_weight = (1 - miner_percentage) * blockchain_importance

        # Ensure the adjusted weight is non-negative
        return max(0, adjusted_weight)

    def calculate_score(self, network, hot_key, model_type, process_time, start_block_height, last_block_height, blockchain_block_height, data_samples_are_valid, run_id):

        multiple_ips = self.miner_registry_manager.detect_multiple_ip_usage(hot_key)
        if multiple_ips:
            return 0

        multiple_run_ids = self.miner_registry_manager.detect_multiple_run_id(run_id)
        if multiple_run_ids:
            return 0

        cheat_factor = self.miner_registry_manager.calculate_cheat_factor(hot_key=hot_key, network=network, model_type=model_type, sample_size=self.config.get_cheat_factor(network))
        miner_distribution = self.miner_registry_manager.get_miner_distribution(self.config.get_network_importance_keys())

        bt.logging.info(f"🔄 Calculating score for parameters:"
                        f"network: {network}, "
                        f"process_time: {process_time}, "
                        f"start_block_height: {start_block_height}, "
                        f"last_block_height: {last_block_height}, "
                        f"blockchain_block_height: {blockchain_block_height},"
                        f"miner_distribution: {miner_distribution}, "
                        f"data_samples_are_valid: {data_samples_are_valid},"
                        f"cheat_factor: {cheat_factor}")

        # Return a score of 0 if the data samples are not valid
        if not data_samples_are_valid:
            return 0

        bt.logging.info(f"Partial results: ")

        # Calculate dynamic weight based on network and miner distribution
        blockchain_size_weight = self.get_dynamic_weight(network, miner_distribution)
        bt.logging.debug(f"Blockchain size weight: {blockchain_size_weight}")

        # Process time scoring logic: Higher score for lower process time
        process_time_score = max(0, min(1, 1.5 - 0.05 * process_time)) # Ensuring the score is between 0 and 1
        bt.logging.debug(f"Process time score: {process_time_score}")

        # Block height difference scoring logic: Lower score for higher block height difference
        block_height_diff = abs(last_block_height - blockchain_block_height)
        block_height_score = max(0, min(1, 1 - block_height_diff / 100))  # Normalizing score to be between 0 and 1
        bt.logging.debug(f"Block height score: {block_height_score}")

        # Block height recency scoring logic: Higher score for more recent data
        block_height_diff_recency = blockchain_block_height - start_block_height
        block_height_recency_score = max(0, min(1, 1 - block_height_diff_recency / self.config.get_block_height_recency_scale_factor(network)))
        #block_height_recency_score = max(0, min(1, 1 - block_height_diff_recency / 50000))  # Normalizing score to be between 0 and 1
        bt.logging.debug(f"Block height recency score: {block_height_recency_score}")

        # Calculate total score using weighted average
        total_score = (process_time_score * self.config.process_time_weight +
                       block_height_score * self.config.block_height_diff_weight +
                       blockchain_size_weight * self.config.blockchain_importance_weight +
                       block_height_recency_score * self.config.block_height_recency_weight +
                       max(0, 1 - cheat_factor) * self.config.cheat_factor_weight)  # Ensuring cheat factor reduces the score
        bt.logging.debug(f"Total score: {total_score}")

        # Normalize the score to be within 0 to 1 range
        max_possible_score = self.config.process_time_weight + self.config.block_height_diff_weight + self.config.blockchain_importance_weight + block_height_recency_score + self.config.cheat_factor_weight
        normalized_score = total_score / max_possible_score
        normalized_score = min(max(normalized_score, 0), 1)  # Ensuring the score is within 0 to 1
        bt.logging.info(f"Final normalized score: {normalized_score}")

        return normalized_score