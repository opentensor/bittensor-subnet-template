import unittest

from neurons.validators.scoring import calculate_score

class MockDendrite:
    def __init__(self, process_time):
        self.process_time = process_time

class ResponseMock:
    def __init__(self, process_time, block_height, data_sample_is_valid):
        self.dendrite = MockDendrite(process_time)
        self.block_height = block_height
        self.data_sample_is_valid = data_sample_is_valid


class TestCalculateScore(unittest.TestCase):
    def setUp(self):
        # Setup mock responses for testing
        self.valid_response = ResponseMock(1, 100, True)
        self.high_latency_response = ResponseMock(5, 100, True)
        self.incorrect_data_response = ResponseMock(1, 100, False)
        self.far_behind_response = ResponseMock(1, 300, True)
        self.slightly_behind_response = ResponseMock(1, 150, True)


    def test_monster_bitcoin_miner(self):
        response = ResponseMock(500, 99, True)
        score = calculate_score(response, 100, 'doge')
        self.assertGreater(score, 0, "Score should be positive for valid response")

    def test_valid_response(self):
        score = calculate_score(self.valid_response, 100, 1)
        self.assertGreater(score, 0, "Score should be positive for valid response")

    def test_high_latency_response(self):
        score = calculate_score(self.high_latency_response, 100, 1)
        self.assertLess(score, 1, "Score should decrease with higher latency")

    def test_incorrect_data_response(self):
        score = calculate_score(self.incorrect_data_response, 100, 1)
        self.assertEqual(score, 0, "Score should be zero for incorrect data")

    def test_far_behind_response(self):
        score = calculate_score(self.far_behind_response, 100, 1)
        self.assertLess(score, 1, "Score should decrease significantly if far behind")

    def test_slightly_behind_response(self):
        score = calculate_score(self.slightly_behind_response, 100, 1)
        self.assertLess(score, 1, "Score should decrease slightly if slightly behind")

    def test_blockchain_importance(self):
        bitcoin_score = calculate_score(self.valid_response, 100, 3)
        ltc_score = calculate_score(self.valid_response, 100, 2)
        self.assertGreater(bitcoin_score, ltc_score, "Bitcoin should have a higher score due to greater importance")

if __name__ == '__main__':
    unittest.main()
