import unittest
from unittest.mock import MagicMock
from neurons.validators.utils.uids import check_uid_availability, get_random_uids

class TestYourClass(unittest.TestCase):

    def test_check_uid_availability(self):
        metagraph = MagicMock()
        axon_mock = MagicMock()
        neuron_mock = MagicMock()
        
        uid = 123  # Replace with a valid uid for testing
        vpermit_tao_limit = 10  # Replace with a valid vpermit_tao_limit for testing

        # Configure mocks
        metagraph.axons.__getitem__.return_value = axon_mock
        metagraph.validator_permit.__getitem__.return_value = True  # Adjust as needed
        metagraph.S.__getitem__.return_value = 5  # Replace with a valid value for testing
        metagraph.neurons.__getitem__.return_value = neuron_mock
        neuron_mock.axon_info.ip = '192.168.1.1'  # Replace with a valid IP for testing

        # Assuming the method is standalone (not part of a class)
        result = check_uid_availability(metagraph, uid, vpermit_tao_limit)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
