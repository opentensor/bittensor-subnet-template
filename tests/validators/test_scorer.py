import unittest
from unittest.mock import MagicMock
from neurons.remote_config import ValidatorConfig
from neurons.validators.miner_registry import MinerRegistryManager
from neurons.validators.scoring import Scorer


class TestScorer(unittest.TestCase):
    def setUp(self):
        self.miner_registry_manager = MagicMock(spec=MinerRegistryManager)
        self.validator_config = ValidatorConfig()
        
        self.validator_config.blockchain_importance_weight = 0.3
        self.validator_config.block_height_recency_weight = 0.2
        self.validator_config.block_height_weight = 0.7
        self.validator_config.process_time_weight = 0.1
        self.validator_config.discovery_timeout = 100
        self.validator_config.blockchain_importance = {'bitcoin': 0.9, 'doge': 0.1}

        self.scorer = Scorer(self.validator_config)


    def test_final_score(self):
        score_cases = [
            {"process_time_score": 0, "block_height_score": 1, "block_height_recency_score": 1, "blockchain_score":1},
            {"process_time_score": 1, "block_height_score": 0, "block_height_recency_score": 1, "blockchain_score":1},
            {"process_time_score": 1, "block_height_score": 1, "block_height_recency_score": 0, "blockchain_score":1},
            {"process_time_score": 1, "block_height_score": 1, "block_height_recency_score": 1, "blockchain_score":1},
        ]

        for case in score_cases:
            with self.subTest(case=case):
                score = self.scorer.final_score(
                    process_time_score=case["process_time_score"],
                    block_height_score=case["block_height_score"],
                    block_height_recency_score=case["block_height_recency_score"],
                    blockchain_score = case['blockchain_score']
                )
                if case["process_time_score"] == 0 or case["block_height_recency_score"] == 0 or case["block_height_score"] == 0:
                    assert score == 0
                else:
                    assert score != 0


    def test_calculate_process_time_score(self):
        timeout = 3
        cases = [1, 2, 3, 4]
        for process_time in cases:
            with self.subTest(process_time = process_time):
                score = self.scorer.calculate_process_time_score(process_time, timeout)
                if process_time < timeout:
                    assert score > 0
                else:
                    assert score == 0
        
        with self.subTest():
            score1 = self.scorer.calculate_process_time_score(1, timeout)
            score2 = self.scorer.calculate_process_time_score(2, timeout)
            assert score1 > score2


    def test_calculate_block_height_score(self):

        with self.subTest(test_case="diff_less_than_min_blocks"):
            score = self.scorer.calculate_block_height_score(network="bitcoin", indexed_start_block_height=5, indexed_end_block_height=8, blockchain_block_height=15)
            assert score == 0
        
        with self.subTest(test_case="diff_gt_than_min_blocks"):
            score = self.scorer.calculate_block_height_score(network="bitcoin", indexed_start_block_height=700_000, indexed_end_block_height=800_000, blockchain_block_height=800_000)
            assert score > 0

        with self.subTest(test_case="recent_block_should_have_higher_score"):
            score1 = self.scorer.calculate_block_height_score(network="bitcoin", indexed_start_block_height=700_000, indexed_end_block_height=800_000, blockchain_block_height=800_000)
            score2 = self.scorer.calculate_block_height_score(network="bitcoin", indexed_start_block_height=600_000, indexed_end_block_height=700_000, blockchain_block_height=800_000)
            assert score1 > score2

    def test_calculate_block_height_recency_score(self):
        with self.subTest(test_case="score_between_0_and_1"):
            score1 = self.scorer.calculate_block_height_recency_score(network='bitcoin', indexed_end_block_height=10, blockchain_block_height=10) 
            assert score1 == 1

            score2 = self.scorer.calculate_block_height_recency_score(network='bitcoin', indexed_end_block_height=0, blockchain_block_height=10)
            assert score2 == 0

        with self.subTest(test_case="recent_block_should_have_higher_score"):
            score1 = self.scorer.calculate_block_height_recency_score(network='bitcoin', indexed_end_block_height=5, blockchain_block_height=10)
            score2 = self.scorer.calculate_block_height_recency_score(network='bitcoin', indexed_end_block_height=4, blockchain_block_height=10)
            assert score1 > score2

    def test_calculate_blockchain_weight(self):
        with self.subTest(test_case="unique_blockchain_distribution_should_return_1"):
            score = self.scorer.calculate_blockchain_weight("bitcoin", miner_distribution={'bitcoin':256})
            assert score == 1
        
        with self.subTest(test_case="when_miner_are_under_represented_then_score_should_be_higher"):
            score1 = self.scorer.calculate_blockchain_weight("bitcoin", miner_distribution={'bitcoin':1, 'doge': 99})
            score2 = self.scorer.calculate_blockchain_weight("bitcoin", miner_distribution={'bitcoin':50, 'doge': 50})
            assert score1 > score2
        with self.subTest(test_case="when_miner_are_over_represented_then_score_should_be_same"):
            score1 = self.scorer.calculate_blockchain_weight("bitcoin", miner_distribution={'bitcoin':91, 'doge': 9})
            score2 = self.scorer.calculate_blockchain_weight("bitcoin", miner_distribution={'bitcoin':95, 'doge': 5})
            assert score1 == score2

if __name__ == '__main__':
    unittest.main()
