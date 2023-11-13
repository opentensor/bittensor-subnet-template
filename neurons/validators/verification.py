import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BLOCKCHAIR_API_KEY", "xxx")


def get_latest_block_height(network):
    url = f"https://api.blockchair.com/{network.lower()}/stats?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        latest_block_height = data["data"]["blocks"]
        return latest_block_height
    else:
        raise Exception(f"Failed to fetch data: HTTP {response.status_code}")


def verify_data_sample(network, input_result):
    url = f"https://api.blockchair.com/{network.lower()}/dashboards/block/{input_result.block_height}?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        block_data = response.json()
        block_info = block_data["data"][str(input_result.block_height)]["block"]
        num_transactions = block_info["transaction_count"]
        total_sent = block_info["output_total"]
        result = {
            "block_height": input_result.block_height,
            "total_value_satoshi": total_sent,
            "transaction_count": num_transactions,
        }
        return result == input_result

    else:
        raise Exception(f"Failed to fetch data: HTTP {response.status_code}")
