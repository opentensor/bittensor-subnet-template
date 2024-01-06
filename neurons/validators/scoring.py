import bittensor as bt
from neurons.remote_config import ValidatorConfig

class Scorer:
    def __init__(self, config: ValidatorConfig):
        self.config = config

    def calculate_score(self, network,  process_time, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height, data_samples_are_valid, miner_distribution, multiple_ips, multiple_run_ids):
        log =  (f'🔄 Network: {network} | ' \
                f'Process time: {process_time:4f} | ' \
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
        blockchain_score = self.calculate_blockchain_weight(network, miner_distribution)

        final_score = self.final_score(process_time_score, block_height_score, block_height_recency_score, blockchain_score)

        log =  (f'🔄 Process time score: {process_time_score:.4f} | ' \
                f'Block height score: {block_height_score:.4f} | ' \
                f'Block height recency score: {block_height_recency_score:.4f} | ' \
                f'Blockchain score: {blockchain_score:.4f} | ' \
                f'Final score: {final_score:.4f} |')
        bt.logging.info(log)
        return final_score

    def final_score(self, process_time_score, block_height_score, block_height_recency_score, blockchain_score):

        if process_time_score == 0 or block_height_score == 0 or block_height_recency_score == 0:
            return 0

        total_score = (
            process_time_score * self.config.process_time_weight +
            block_height_score * self.config.block_height_weight +
            block_height_recency_score * self.config.block_height_recency_weight +
            blockchain_score * self.config.blockchain_importance_weight
        )

        total_weights = (
            self.config.process_time_weight +
            self.config.block_height_weight +
            self.config.block_height_recency_weight +
            self.config.blockchain_importance_weight
        )

        normalized_score = total_score / total_weights
        normalized_score = min(max(normalized_score, 0), 1)  # Ensuring the score is within 0 to 1
        return normalized_score


    def calculate_process_time_score(self, process_time, discovery_timeout):
        process_time = min(process_time, discovery_timeout)
        factor = (process_time / discovery_timeout) ** 2
        process_time_score = max(0, 1 - factor)
        return process_time_score


    def calculate_block_height_recency_score(self, network, indexed_end_block_height, blockchain_block_height):
        recency_diff = blockchain_block_height - indexed_end_block_height

        recency_score = max(0, (1 - recency_diff / blockchain_block_height) ** self.config.get_blockchain_recency_weight(network))
        
        return recency_score


    def calculate_block_height_score(self, network, indexed_start_block_height: int, indexed_end_block_height: int, blockchain_block_height: int):

        covered_blocks = indexed_end_block_height - indexed_start_block_height

        min_blocks = self.config.get_blockchain_min_blocks(network=network)
        if covered_blocks < min_blocks:
            return 0

        coverage_percentage = covered_blocks / blockchain_block_height

        #Amplifying the impact of small values.
        coverage_percentage = coverage_percentage ** 0.6

        recency_score = self.calculate_block_height_recency_score(network, indexed_end_block_height, blockchain_block_height)
        overall_score = 0.8 * coverage_percentage + 0.2 * recency_score

        return overall_score


    def calculate_blockchain_weight(self, network, miner_distribution):
        
        if len(miner_distribution) == 1:
            return 1
        
        importance = self.config.get_network_importance(network)

        miners_actual_distribution = miner_distribution[network] / sum(miner_distribution.values())
        miners_distribution_score = max(0, -(miners_actual_distribution - importance))

        overall_score = importance + 0.2 * miners_distribution_score

        return overall_score