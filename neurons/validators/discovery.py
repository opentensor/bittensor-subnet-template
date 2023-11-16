from random import randint
from neurons.validators.blockchair_api import BlockchairAPI


class BlockVerification:

    def __init__(self, api_key: str = None):
        self.blochair_api = BlockchairAPI(api_key)

    def get_verification_data(self) -> dict[str, dict]:
        network = 'bitcoin'
        last_block_height = self.blochair_api.get_latest_block_height(
            network=network
        )
        random_block_height = randint(1, last_block_height-100)
        result: dict[dict] = { network: {
            'funds_flow': random_block_height,
            'last_block_height': last_block_height
        }}

        return result

    def verify_data_sample(self, network, block_height, input_result):
        data_sample_is_valid = self.blochair_api.verify_data_sample(
            network=network,
            block_height=block_height,
            input_result=input_result,
        )

        return data_sample_is_valid