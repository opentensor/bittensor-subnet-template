import unittest
import time
from neurons.remote_config import ValidatorConfig
from neurons.validators.scoring import Scorer

class TestScoreCalculation(unittest.TestCase):
    def setUp(self):
        self.config = ValidatorConfig()
        self.config.load_and_get_config_values()
        time.sleep(5)
        self.multiple_ips, self.multiple_run_ids = False, False
        self.miner_distribution = {'bitcoin': 180}

    """
    ------------------------ moja chyba
    Calculating score for parameters:network: bitcoin, process_time: 53.230361461639404, start_block_height: 769787, last_block_height: 793298, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 179}, data_samples_are_valid: True,cheat_factor: 0
    2023-12-28 20:49:32.077 |       INFO       | Final normalized score: 0.30927835051546393
      
      """

    def test_calculate_score_1(self):
        """
        Calculating score for parameters:network: bitcoin, process_time: 3.8282129764556885, start_block_height: 769787, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
        2023-12-28 20:50:11.521 |       INFO       | Final normalized score: 0.905154639175258
        after change 0.45
        """
        self.config.block_height_weight = 3
        self.config.process_time_weight = 1
        self.config.block_height_recency_weight = 1

        scorer = Scorer(self.config)
        score = scorer.calculate_score(
            network="bitcoin",
            process_time=3.8282129764556885,
            indexed_start_block_height=769787,
            indexed_end_block_height=823300,
            blockchain_last_block_height=823312,
            data_samples_are_valid=True,
            miner_distribution=self.miner_distribution,
            multiple_ips=self.multiple_ips,
            multiple_run_ids=self.multiple_run_ids
        )

        print(f"score: {score}")
        self.assertLess(score, 0.905154639175258)

    def test_calculate_score_2(self):
        """
        Calculating score for parameters:network: bitcoin, process_time: 3.3934412002563477, start_block_height: 822800, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
        2023-12-28 20:50:03.195 |       INFO       | Final normalized score: 0.905154639175258
        after change 0.45
        """

        self.config.block_height_weight = 3
        self.config.process_time_weight = 1
        self.config.block_height_recency_weight = 1

        scorer = Scorer(self.config)
        score = scorer.calculate_score(
            network="bitcoin",
            process_time=3.3934412002563477,
            indexed_start_block_height=822800,
            indexed_end_block_height=823300,
            blockchain_last_block_height=823312,
            data_samples_are_valid=True,
            miner_distribution=self.miner_distribution,
            multiple_ips=self.multiple_ips,
            multiple_run_ids=self.multiple_run_ids
        )

        print(f"score: {score}")
        self.assertLess(score, 0.905154639175258)

    def test_calculate_score_3(self):
        """
        Calculating score for parameters:network: bitcoin, process_time: 3.3934412002563477, start_block_height: 822800, last_block_height: 823300, blockchain_block_height: 823312,miner_distribution: {'bitcoin': 180}, data_samples_are_valid: True,cheat_factor: 0
        2023-12-28 20:50:03.195 |       INFO       | Final normalized score: 0.905154639175258
        after change 0.45
        """

        self.config.block_height_weight = 3
        self.config.process_time_weight = 1
        self.config.block_height_recency_weight = 1

        scorer = Scorer(self.config)
        score = scorer.calculate_score(
            network="bitcoin",
            process_time=82.50597262382507,
            indexed_start_block_height=769787,
            indexed_end_block_height=823300,
            blockchain_last_block_height=823312,
            data_samples_are_valid=True,
            miner_distribution=self.miner_distribution,
            multiple_ips=self.multiple_ips,
            multiple_run_ids=self.multiple_run_ids
        )

        print(f"score: {score}")
        self.assertLess(score, 0.8536082474226806)

if __name__ == '__main__':
    unittest.main()
