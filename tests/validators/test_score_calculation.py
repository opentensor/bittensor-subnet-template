import unittest
import time
from neurons.remote_config import ValidatorConfig
from neurons.validators.scoring import Scorer
import pandas as pd

class TestScoreCalculation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = ValidatorConfig()
        cls.config.load_and_get_config_values()
        time.sleep(5)

        cls.config.discovery_timeout = 100
        cls.config.process_time_weight = 1
        cls.config.block_height_weight = 100
        cls.block_height_recency_weight = 10

        #cls.blockchain_importance = { "bitcoin": 0.9, "doge": 0.1 }

        cls.test_results = []

    @staticmethod
    def generate_test_cases():
        network_distribution = {'bitcoin': 256 }
        cases = [
            # block height score
            ("bitcoin", 50, 769787, 823914, 823914, network_distribution),

            ("bitcoin", 10, 1, 790000, 800000, network_distribution),
            ("bitcoin", 10, 780000, 790000, 800000, network_distribution),
            ("bitcoin", 10, 700000, 790000, 800000, network_distribution),
            ("bitcoin", 10, 600000, 790000, 800000, network_distribution),
            ("bitcoin", 10, 400000, 790000, 800000, network_distribution),

            # block height score + process time score
            ("bitcoin", 50, 600000, 790000, 800000, network_distribution),
            ("bitcoin", 75, 600000, 790000, 800000, network_distribution),
            ("bitcoin", 99, 600000, 790000, 800000, network_distribution),

            # block height score + process time score + block height recency score
            ("bitcoin", 50, 600000, 750000, 800000, network_distribution),
            ("bitcoin", 75, 600000, 720000, 800000, network_distribution),
            ("bitcoin", 99, 600000, 700000, 800000, network_distribution),
        ]

        cases.extend([
            # Real life cases
            ("bitcoin", 86.12195301055908, 769787, 803768, 823387, {'bitcoin': 192}),
            ("bitcoin", 4.060604095458984, 769787, 823374, 823387, {'bitcoin': 192}),
            ("bitcoin", 93.75491285324097, 769787, 823375, 823387, {'bitcoin': 192}),
            ("bitcoin", 81.23294234275818, 769787, 782735, 823387, {'bitcoin': 192}),
            ("bitcoin", 4.6733479499816895, 822800, 823374, 823387, {'bitcoin': 191}),
            ("bitcoin", 2.4628868103027344, 823260, 823374, 823386, {'bitcoin': 191})
        ])

        return cases

    def test_calculate_scores(self):
        for case in self.generate_test_cases():
            with self.subTest(case=case):
                network, process_time, start_block, end_block, blockchain_height, miner_distribution = case

                scorer = Scorer(self.config)
                score = scorer.calculate_score(
                    network=network,
                    process_time=process_time,
                    indexed_start_block_height=start_block,
                    indexed_end_block_height=end_block,
                    blockchain_last_block_height=blockchain_height,
                    data_samples_are_valid=True,
                    miner_distribution=miner_distribution,
                    multiple_ips=False,
                    multiple_run_ids=False,
                )

                result = {
                    "network": network,
                    "process_time": process_time,
                    "start_block": start_block,
                    "end_block": end_block,
                    "blockchain_height": blockchain_height,
                    "miner_distribution": miner_distribution,
                    "calculated_score": score
                }
                self.test_results.append(result)

        time.sleep(3)
        # Set pandas display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)

        print("Summary:")
        df = pd.DataFrame(self.test_results)
        print(df)
        df_sorted = df.sort_values(by='calculated_score', ascending=False)
        # print(df_sorted)

        print("Weight values:")
        print(f"process_time_weight: {self.config.process_time_weight}")
        print(f"block_height_weight: {self.config.block_height_weight}")
        print(f"block_height_recency_weight: {self.config.block_height_recency_weight}")
        print(f"discovery_timeout: {self.config.discovery_timeout}")

if __name__ == '__main__':
    unittest.main()

# start_block_height: 823827, last_block_height: 823852, blockchain_block_height: 823864,