import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session_with_retries():
    session = requests.Session()
    retries = Retry(
        total=None,  # Infinite retries
        backoff_factor=1,  # Increase delay between retries
        status_forcelist=[500, 502, 503, 504],  # Retry for these status codes
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


class BlockchairAPI:
    def __init__(self, api_key):
        if api_key is None:
            self.api_key = os.getenv("BLOCKCHAIN_API_KEY", "A___mw5wNljHQ4n0UAdM5Ivotp0Bsi93")
        else:
            self.api_key = api_key
        self.session = create_session_with_retries()

    def get_latest_block_height(self, network):
        url = f"https://api.blockchair.com/{network.lower()}/stats?key={self.api_key}"
        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            latest_block_height = data["data"]["blocks"]
            return latest_block_height
        else:
            raise BlockchairAPIError(f"Failed to fetch data: HTTP {response.status_code}", response.status_code)

    def verify_data_sample(self, network, input_result):
        block_height = int(input_result['block_height'])
        url = f"https://api.blockchair.com/{network.lower()}/dashboards/block/{block_height}?key={self.api_key}"
        response = self.session.get(url)
        if response.status_code == 200:
            try:
                block_data = response.json()
                block_height_str = str(block_height)
                block_info = block_data["data"][block_height_str]["block"]
                num_transactions = block_info["transaction_count"]
                total_sent = block_info["output_total"]
                result = {
                    "block_height": block_height,
                    "total_value_satoshi": total_sent,
                    "transaction_count": num_transactions,
                }

                is_valid = result["transaction_count"] == input_result["transaction_count"]
                return is_valid
            except KeyError as e:
                return False
        else:
            raise BlockchairAPIError(f"Failed to fetch data: HTTP {response.status_code}", response.status_code)

    def are_all_samples_valid(self, network, data_samples):
        for data_sample in data_samples:
            data_sample_is_valid = self.verify_data_sample(
                network=network,
                input_result=data_sample,
            )
            if not data_sample_is_valid:
                return False
        return True

class BlockchairAPIError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code
