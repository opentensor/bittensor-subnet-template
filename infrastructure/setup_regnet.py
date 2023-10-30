import time
import unittest
from infrastructure.bitcoin_core_utils import execute_bitcoin_cli_command, remove_container, create_and_start_bitcoin_core_container


class BitcoinCoreCliTests(unittest.TestCase):
    container_name = "infrastructure-bitcoin-core-1"

    @classmethod
    def setUpClass(cls):
        remove_container(cls.container_name)
        create_and_start_bitcoin_core_container(cls.container_name)
        time.sleep(10)

    def test_sending_transaction(self):
        # 1. Create wallet
        wallet_name = "testwallet"
        result = execute_bitcoin_cli_command(self.container_name, f"createwallet {wallet_name}")
        print(result.output.decode())

        # 2. Get new address
        address = execute_bitcoin_cli_command(self.container_name, "getnewaddress").output.decode().strip()
        print(f"New address: {address}")

        # 3. Generate blocks (to obtain regtest coins, assuming you're doing this from the start)
        result = execute_bitcoin_cli_command(self.container_name, f"generatetoaddress 101 {address}")
        print(result.output.decode())

        time.sleep(2)

        # 4. Check balance
        balance = execute_bitcoin_cli_command(self.container_name, "getbalance").output.decode().strip()
        print(f"Balance: {balance}")

        # 5. Send coins to another address (e.g., back to the same for demonstration)
        execute_bitcoin_cli_command(self.container_name, "settxfee 0.0002")
        send_amount = "10"
        transaction_id = execute_bitcoin_cli_command(self.container_name, f"sendtoaddress {address} {send_amount}").output.decode().strip()
        print(f"Sent {send_amount} BTC to {address}. Transaction ID: {transaction_id}")
