import unittest
from unittest.mock import MagicMock
from neurons.remote_config import ValidatorConfig
from neurons.validators.miner_registry import MinerRegistryManager
from neurons.validators.scoring import Scorer


"""
Calculating score for parameters:network: bitcoin, process_time: 3.8282129764556885, start_block_height: 769787, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
2023-12-28 20:50:11.521 |       INFO       | Final normalized score: 0.905154639175258
Calculating score for parameters:network: bitcoin, process_time: 3.3934412002563477, start_block_height: 822800, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
2023-12-28 20:50:03.195 |       INFO       | Final normalized score: 0.905154639175258
Calculating score for parameters:network: bitcoin, process_time: 53.230361461639404, start_block_height: 769787, last_block_height: 793298, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 179}, data_samples_are_valid: True,cheat_factor: 0
2023-12-28 20:49:32.077 |       INFO       | Final normalized score: 0.30927835051546393
Calculating score for parameters:network: bitcoin, process_time: 82.50597262382507, start_block_height: 769787, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 179}, data_samples_are_valid: True,cheat_factor: 0
2023-12-28 20:49:22.884 |       INFO       | Final normalized score: 0.8536082474226806


Calculating score for parameters:network: bitcoin, process_time: 3.8282129764556885, start_block_height: 769787, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
Calculating score for parameters:network: bitcoin, process_time: 3.3934412002563477, start_block_height: 822800, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
Calculating score for parameters:network: bitcoin, process_time: 53.230361461639404, start_block_height: 769787, last_block_height: 793298, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 179}, data_samples_are_valid: True,cheat_factor: 0
Calculating score for parameters:network: bitcoin, process_time: 82.50597262382507, start_block_height: 769787, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 179}, data_samples_are_valid: True,cheat_factor: 0
"""

class TestScorer(unittest.TestCase):
    def setUp(self):
        self.miner_registry_manager = MagicMock(spec=MinerRegistryManager)
        self.validator_config = ValidatorConfig()
        self.validator_config.load_and_get_config_values()
        self.scorer = Scorer(self.validator_config, self.miner_registry_manager)


    def test_final_score(self):
        for i in range(1, 10):
            with self.subTest(i=i):
                score = self.scorer.final_score(i, i, i, i, 0)
                print(f"score: {score}")

    def test_calculate_process_time_score(self):
        for i in range(1, 10):
            with self.subTest(i=i):
                score = self.scorer.calculate_process_time_score(i, 10)
                print(f"reposne time: {i} score: {score}")

    def test_calculate_block_height_score(self):
        for i in range(1, 10):
            with self.subTest(i=i):
                indexed_start_block_height = 100
                indexed_end_block_height = 100 + i * 100
                blockchain_last_block_height = 1000
                score = self.scorer.calculate_block_height_score(indexed_start_block_height=indexed_start_block_height,
                                                          indexed_end_block_height=indexed_end_block_height,
                                                          blockchain_last_block_height=blockchain_last_block_height)
                print(f"indexed_start_block_height: {indexed_start_block_height}, indexed_end_block_height: {indexed_end_block_height}, blockchain_last_block_height: {blockchain_last_block_height}, score: {score}")

        indexed_start_block_height = 890
        indexed_end_block_height = 900
        blockchain_last_block_height = 1000

        score = self.scorer.calculate_block_height_score(indexed_start_block_height=indexed_start_block_height,
                                                  indexed_end_block_height=indexed_end_block_height,
                                                  blockchain_last_block_height=blockchain_last_block_height)

        print(f"indexed_start_block_height: {indexed_start_block_height}, indexed_end_block_height: {indexed_end_block_height}, blockchain_last_block_height: {blockchain_last_block_height}, score: {score}")


if __name__ == '__main__':
    unittest.main()
