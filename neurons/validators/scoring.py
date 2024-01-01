import bittensor as bt
from neurons.remote_config import ValidatorConfig
from neurons.validators.miner_registry import MinerRegistryManager

class Scorer:
    def __init__(self, config: ValidatorConfig):
        self.config = config

    def calculate_score(self, network,  process_time, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height, data_samples_are_valid, miner_distribution, multiple_ips, multiple_run_ids):
        log =  (f'🔄 Network: {network} | ' \
                f'Process time: {process_time} | ' \
                f'Indexed start block height: {indexed_start_block_height} | ' \
                f'Indexed end block height: {indexed_end_block_height} | ' \
                f'Blockchain last block height: {blockchain_last_block_height} | ' \
                f'Miner distribution: {miner_distribution} | ' \
                f'Multiple IPs: {multiple_ips} | ' \
                f'Multiple run id: {multiple_run_ids} | ' \
                f'Valid data samples: {data_samples_are_valid} | ')
        bt.logging.info(log)

        if multiple_ips:
            bt.logging.info(f"🔄 Final score: 0")
            return 0
        if multiple_run_ids:
            bt.logging.info(f"🔄 Final score: 0")
            return 0
        if not data_samples_are_valid:
            bt.logging.info(f"🔄 Final score: 0")
            return 0

        process_time_score = self.calculate_process_time_score(process_time, self.config.discovery_timeout)
        block_height_score = self.calculate_block_height_score(network, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height)
        block_height_recency_score = self.calculate_block_height_recency_score(network, indexed_end_block_height, blockchain_last_block_height)
        final_score = self.final_score(process_time_score, block_height_score, block_height_recency_score)

        log =  (f'🔄 Process time score: {process_time_score} | ' \
                f'Block height score: {block_height_score} | ' \
                f'Block height recency score: {block_height_recency_score} | ' \
                f'Final score: {final_score} |')
        bt.logging.info(log)
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

        normalized_score = total_score / total_weights
        normalized_score = min(max(normalized_score, 0), 1)  # Ensuring the score is within 0 to 1
        return normalized_score


    def calculate_process_time_score(self, process_time, discovery_timeout):
        process_time = min(process_time, discovery_timeout)
        factor = (process_time / discovery_timeout) ** 2
        process_time_score = round(max(0, 1 - factor), 4)
        return process_time_score

    def calculate_block_height_recency_score(self, network, indexed_end_block_height, blockchain_block_height):
        block_height_diff_recency = blockchain_block_height - indexed_end_block_height
        block_height_recency_score = max(0, min(1, 1 - block_height_diff_recency / self.config.get_block_height_recency_scale_factor(network)))
        return block_height_recency_score

    def calculate_block_height_score(self, network, indexed_start_block_height: int, indexed_end_block_height: int, blockchain_last_block_height: int):

        diff = indexed_end_block_height - indexed_start_block_height
        min_blocks = self.config.get_blockchain_min_blocks(network=network)
        if diff < min_blocks:
            return 0

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
        return block_height_score


