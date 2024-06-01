import os
import unittest
from neurons.nodes.factory import NodeFactory
from insights.protocol import NETWORK_BITCOIN, Challenge, MODEL_TYPE_FUNDS_FLOW


class TestChallenge(unittest.TestCase):
    def test_solve_challenge(self):

        node = NodeFactory.create_node(NETWORK_BITCOIN)

        challenge = Challenge(model_type=MODEL_TYPE_FUNDS_FLOW, in_total_amount=203216, out_total_amount=200000, tx_id_last_4_chars="d946")
        expected_output = "93fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d946"
        test_output1 = "93fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d945"
        test_output2 = "83fa1edce68762615740fd35581fc337d508ca33e682057bed7b395b5d66d946"

        is_valid = node.validate_challenge_response_output(challenge, expected_output)
        self.assertEqual(is_valid, True)

        is_valid = node.validate_challenge_response_output(challenge, test_output1)
        self.assertEqual(is_valid, False)

        is_valid = node.validate_challenge_response_output(challenge, test_output2)
        self.assertEqual(is_valid, False)


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    unittest.main()