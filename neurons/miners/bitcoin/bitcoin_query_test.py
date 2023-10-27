import unittest
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

RPC_URL = "http://user:password@127.0.0.1:18443"


class BitcoinRegtest(unittest.TestCase):
    def setUp(self):
        self.conn = AuthServiceProxy(RPC_URL)

    def tearDown(self):
        # Clean up any resources or close connections here if needed
        pass

    def test_bitcoin_transaction(self):
        # Create wallets
        wallet1 = self.conn.createwallet("wallet1")
        wallet2 = self.conn.createwallet("wallet2")

        # Get the wallet RPCs
        wallet1_rpc = self.conn.get_wallet_rpc("wallet1")
        wallet2_rpc = self.conn.get_wallet_rpc("wallet2")

        # Generate some blocks to the first wallet to get coins
        address1 = wallet1_rpc.getnewaddress()
        self.conn.generatetoaddress(101, address1)  # Mine 101 blocks

        # Check balance
        balance = wallet1_rpc.getbalance()
        self.assertGreater(balance, 50)  # Assert that we have more than 50 BTC

        # Send bitcoins to the second wallet
        address2 = wallet2_rpc.getnewaddress()
        wallet1_rpc.sendtoaddress(address2, 10)  # Send 10 BTC

        # Generate a block to confirm the transaction
        self.conn.generatetoaddress(1, address1)

        # Check balance of second wallet
        balance_wallet2 = wallet2_rpc.getbalance()
        self.assertEqual(balance_wallet2, 10)  # Assert that we received 10 BTC


if __name__ == "__main__":
    unittest.main()
