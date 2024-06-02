from neurons.remote_config import ValidatorConfig
from neurons import logger


class Scorer:
    def __init__(self, config: ValidatorConfig):
        self.config = config

    def calculate_score(self, hotkey, network,  process_time, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height, miner_distribution, uptime_avg, worst_end_block_height):
        process_time_score = self.calculate_process_time_score(process_time, self.config.benchmark_timeout)
        block_height_score = self.calculate_block_height_score(network, indexed_start_block_height, indexed_end_block_height, blockchain_last_block_height)
        block_height_recency_score = self.calculate_block_height_recency_score(indexed_end_block_height, blockchain_last_block_height, worst_end_block_height)
        blockchain_score = self.calculate_blockchain_weight(network, miner_distribution)
        uptime_score = self.calculate_uptime_score(uptime_avg)
        final_score = self.final_score(process_time_score, block_height_score, block_height_recency_score, blockchain_score, uptime_score)

        logger.info("Score calculated",
                    hotkey=hotkey,
                    benchmark_process_time=process_time,
                    indexed_start_block_height=indexed_start_block_height,
                    indexed_end_block_height=indexed_end_block_height,
                    blockchain_last_block_height=blockchain_last_block_height,
                    miner_distribution=miner_distribution,
                    uptime_avg=uptime_avg,
                    benchmark_process_time_score=process_time_score,
                    block_height_score=block_height_score,
                    block_height_recency_score=block_height_recency_score,
                    blockchain_score=blockchain_score,
                    uptime_score=uptime_score,
                    final_score=final_score)

        return final_score

    def final_score(self, process_time_score, block_height_score, block_height_recency_score, blockchain_score, uptime_score):

        if process_time_score == 0 or block_height_score == 0 or block_height_recency_score == 0:
            return 0

        total_score = (
            process_time_score * self.config.process_time_weight +
            block_height_score * self.config.block_height_weight +
            block_height_recency_score * self.config.block_height_recency_weight +
            blockchain_score * self.config.blockchain_importance_weight +
            uptime_score * self.config.uptime_weight
        )

        total_weights = (
            self.config.process_time_weight +
            self.config.block_height_weight +
            self.config.block_height_recency_weight +
            self.config.blockchain_importance_weight +
            self.config.uptime_weight
        )

        normalized_score = total_score / total_weights
        normalized_score = min(max(normalized_score, 0), 1)  # Ensuring the score is within 0 to 1
        return normalized_score

    @staticmethod
    def get_performance_score(process_time, best_time, worst_time, timeout):
        if process_time >= timeout:
            return 0  # Timeout case
        if process_time <= best_time:
            return 1  # Best performance case

        # Calculate the normalized score between best_time and worst_time
        normalized_score = 0.1 + 0.9 * (worst_time - process_time) / (worst_time - best_time)
        return max(0.1, min(normalized_score, 1))  # Ensure the score is between 0.1 and 1

    def calculate_process_time_score(self, process_time, discovery_timeout):
        # Define the best and worst process times
        best_time = self.config.min_time 
        worst_time = self.config.max_time
        
        # Use the new performance scoring method
        process_time_score = self.get_performance_score(process_time, best_time, worst_time, discovery_timeout)
        return process_time_score

    @staticmethod
    def calculate_block_height_recency_score(indexed_end_block_height, blockchain_block_height, worst_end_block_height):

        # this is done to ensure that the worst miner does not obtain a score of 0
        min_recency = worst_end_block_height - 100
        if indexed_end_block_height < min_recency:
            return 0

        recency_diff = blockchain_block_height - indexed_end_block_height
        recency_score = max(0, (1 - recency_diff / (blockchain_block_height-min_recency)) ** 4)
        return recency_score

    def calculate_block_height_score(self, network, indexed_start_block_height: int, indexed_end_block_height: int, blockchain_block_height: int):

        covered_blocks = indexed_end_block_height - indexed_start_block_height

        min_blocks = self.config.get_blockchain_min_blocks(network=network)
        if covered_blocks < min_blocks:
            return 0

        coverage_percentage = (covered_blocks-min_blocks) / (blockchain_block_height-min_blocks)
        coverage_percentage = coverage_percentage ** 3
        return coverage_percentage

    def calculate_blockchain_weight(self, network, miner_distribution):

        if len(miner_distribution) == 1:
            return 1

        importance = self.config.get_network_importance(network)

        miners_actual_distribution = miner_distribution[network] / sum(miner_distribution.values())
        miners_distribution_score = max(0, -(miners_actual_distribution - importance))

        overall_score = importance + 0.2 * miners_distribution_score

        return overall_score

    @staticmethod
    def calculate_uptime_score(uptime_avg):
        return uptime_avg
