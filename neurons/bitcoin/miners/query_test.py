import time
import unittest

from bitcoinrpc.authproxy import AuthServiceProxy

from infrastructure.bitcoin_core_utils import execute_bitcoin_cli_command, remove_container, \
    create_and_start_bitcoin_core_container
from neurons.bitcoin.miners.query import BitcoinQuery, BitcoinNodeConfig

RPC_URL = "http://bitcoinrpc:rpcpassword@127.0.0.1:18443"



class RpcIntegrationTest(unittest.TestCase):
    container_name = "infrastructure-bitcoin-core-1"

    @classmethod
    def tearDownClass(cls):
        remove_container(cls.container_name)
        time.sleep(3)

    @classmethod
    def setUpClass(cls):
        remove_container(cls.container_name)
        create_and_start_bitcoin_core_container(cls.container_name)
        time.sleep(10)

    def test_rpc(self):
        rpc_connection = AuthServiceProxy(RPC_URL)
        r1 = rpc_connection.getblockcount()
        print(r1)
        r2 = rpc_connection.getblockchaininfo()['blocks']
        print(r2)

class BitcoinQueryTest(unittest.TestCase):
    container_name = "infrastructure-bitcoin-core-1"

    @classmethod
    def tearDownClass(cls):
        remove_container(cls.container_name)
        time.sleep(3)


    @classmethod
    def setUpClass(cls):
        remove_container(cls.container_name)
        create_and_start_bitcoin_core_container(cls.container_name)
        time.sleep(10)
        wallet_name = "testwallet"
        execute_bitcoin_cli_command(cls.container_name, f"createwallet {wallet_name}")
        cls.address0 = execute_bitcoin_cli_command(cls.container_name, "getnewaddress").output.decode().strip()
        cls.address1 = execute_bitcoin_cli_command(cls.container_name, "getnewaddress").output.decode().strip()
        cls.address2 = execute_bitcoin_cli_command(cls.container_name, "getnewaddress").output.decode().strip()
        cls.address3 = execute_bitcoin_cli_command(cls.container_name, "getnewaddress").output.decode().strip()
        cls.address4 = execute_bitcoin_cli_command(cls.container_name, "getnewaddress").output.decode().strip()

        execute_bitcoin_cli_command(cls.container_name, f"generatetoaddress 101 {cls.address1}")
        execute_bitcoin_cli_command(cls.container_name, f"generatetoaddress 101 {cls.address2}")
        execute_bitcoin_cli_command(cls.container_name, f"generatetoaddress 101 {cls.address3}")
        execute_bitcoin_cli_command(cls.container_name, f"generatetoaddress 101 {cls.address4}")

    def test_query(self):
        execute_bitcoin_cli_command(self.container_name, "settxfee 0.0002")
        execute_bitcoin_cli_command(self.container_name, f"sendtoaddress {self.address1} 1")
        execute_bitcoin_cli_command(self.container_name, f"sendtoaddress {self.address2} 2")
        execute_bitcoin_cli_command(self.container_name, f"sendtoaddress {self.address3} 3")
        execute_bitcoin_cli_command(self.container_name, f"sendtoaddress {self.address4} 4")
        time.sleep(2)
        execute_bitcoin_cli_command(self.container_name, f"generatetoaddress 0 {self.address0}")
        block_hash = execute_bitcoin_cli_command(self.container_name, "getbestblockhash").output.decode().strip()
        block = execute_bitcoin_cli_command(self.container_name, f"getblock {block_hash} 2").output.decode().strip()

        print(block_hash)
        print(block)

        query = BitcoinQuery(BitcoinNodeConfig(RPC_URL))

        result = query.execute(0, 200)
        print(result)
