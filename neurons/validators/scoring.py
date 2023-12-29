import bittensor as bt
from neurons.remote_config import ValidatorConfig
from neurons.validators.miner_registry import MinerRegistryManager

class Scorer:
    def __init__(self, config: ValidatorConfig):
        self.config = config

    def calculate_score(self, network,  process_time, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height, data_samples_are_valid, miner_distribution, multiple_ips, multiple_run_ids):
        bt.logging.info(f"🔄 Calculating score for parameters:"
                        f"network: {network}, "
                        f"process_time: {process_time}, "
                        f"indexed_start_block_height: {indexed_start_block_height}, "
                        f"indexed_end_block_height: {indexed_end_block_height}, "
                        f"blockchain_last_block_height: {blockchain_last_block_height},"
                        f"miner_distribution: {miner_distribution}, "
                        f"data_samples_are_valid: {data_samples_are_valid}")

        if multiple_ips:
            return 0
        if multiple_run_ids:
            return 0
        if not data_samples_are_valid:
            return 0

        bt.logging.info(f"Partial results: ")

        process_time_score = self.calculate_process_time_score(process_time, self.config.discovery_timeout)
        block_height_score = self.calculate_block_height_score(indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height)
        block_height_recency_score = self.calculate_block_height_recency_score(network, indexed_end_block_height, blockchain_last_block_height)

        final_score = self.final_score(process_time_score, block_height_score, block_height_recency_score)
        return final_score

    def final_score(self, process_time_score, block_height_score, block_height_recency_score):

        total_score = (
                process_time_score * self.config.process_time_weight +
                block_height_score * self.config.block_height_weight +
                block_height_recency_score * self.config.block_height_recency_weight
        )

        total_weights = (
                self.config.process_time_weight +
                self.config.block_height_weight +
                self.config.block_height_recency_weight
        )

        bt.logging.debug(f"Total score: {total_score}, Total weights: {total_weights}")

        normalized_score = total_score / total_weights
        normalized_score = min(max(normalized_score, 0), 1)  # Ensuring the score is within 0 to 1
        return normalized_score


    def calculate_process_time_score(self, process_time, discovery_timeout):
        process_time = min(process_time, discovery_timeout)
        factor = (process_time / discovery_timeout) ** 2
        process_time_score = round(max(0, 1 - factor), 4)
        bt.logging.debug(f"Process time score: {process_time_score}")
        return process_time_score

    def calculate_block_height_recency_score(self, network, indexed_end_block_height, blockchain_block_height):
        block_height_diff_recency = blockchain_block_height - indexed_end_block_height
        block_height_recency_score = max(0, min(1, 1 - block_height_diff_recency / self.config.get_block_height_recency_scale_factor(network)))
        bt.logging.debug(f"Block height recency score: {block_height_recency_score}")
        return block_height_recency_score

    def calculate_block_height_score(self, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height):
        # Coverage Percentage
        total_blocks = blockchain_last_block_height
        covered_blocks = indexed_end_block_height - indexed_start_block_height
        coverage_percentage = covered_blocks / total_blocks

        # Recency Score
        recency_diff = blockchain_last_block_height - indexed_end_block_height
        recency_score = max(0, min(1, 1 - (recency_diff / total_blocks)))

        # Overall Score with Pareto Weights
        overall_score = 0.9 * coverage_percentage + 0.1 * recency_score
        block_height_score = round(overall_score, 4)
        bt.logging.debug(f"Block height score: {block_height_score}")
        return block_height_score


