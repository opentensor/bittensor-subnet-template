import unittest

from neurons.validators.validator import Validator


class TestValidateBlockchainRange(unittest.TestCase):

    def test_valid_range(self):
        self.assertTrue(Validator.validate_blockchain_range(1, 100, 10, 200))

    def test_start_block_none(self):
        self.assertFalse(Validator.validate_blockchain_range(None, 100, 10, 200))

    def test_last_block_none(self):
        self.assertFalse(Validator.validate_blockchain_range(1, None, 10, 200))

    def test_negative_start_block(self):
        self.assertFalse(Validator.validate_blockchain_range(-1, 100, 10, 200))

    def test_negative_last_block(self):
        self.assertFalse(Validator.validate_blockchain_range(1, -100, 10, 200))

    def test_start_greater_than_last(self):
        self.assertFalse(Validator.validate_blockchain_range(100, 1, 10, 200))

    def test_min_range_size_not_truthy(self):
        self.assertFalse(Validator.validate_blockchain_range(1, 100, 0, 200))

    def test_last_block_too_high(self):
        self.assertFalse(Validator.validate_blockchain_range(1, 205, 10, 200))

    def test_range_size_too_small(self):
        self.assertFalse(Validator.validate_blockchain_range(1, 10, 15, 200))


if __name__ == '__main__':
    unittest.main()