import os
from bitcoinrpc.authproxy import AuthServiceProxy


class BitcoinNodeConfig:
    def __init__(self, rpc_url: str = None):
        if rpc_url is None:
            self.rpc_url = os.getenv("BITCOIN_RPC_URL", "http://bitcoinrpc:rpcpassword@127.0.0.1:18443")
        else:
            self.rpc_url = rpc_url


class BitcoinQuery:

    def __init__(self, config: BitcoinNodeConfig):
        self.config = config

    def is_synced(self):
        rpc_connection = AuthServiceProxy(self.config.rpc_url)
        return rpc_connection.getblockcount() == rpc_connection.getblockchaininfo()['blocks']


    def get_transactions_from_block_height(self, block_height, rpc_url):
        rpc_connection = AuthServiceProxy(rpc_url)
        block_hash = rpc_connection.getblockhash(block_height)
        block_data = rpc_connection.getblock(block_hash, 2)
        txs = block_data['tx']
        return txs


    def get_transactions_from_block_range(self, start_height, end_height, rpc_url):
        all_transactions = []

        for block_height in range(start_height, end_height + 1):
            txs = self.get_transactions_from_block_height(block_height, rpc_url)
            all_transactions.extend((block_height, txs))

        return all_transactions

    def execute(self, cypher_query) -> list:
        if not self.is_synced():
            raise Exception("Bitcoin node is not synced")
        else:
            return [] # self.get_transactions_from_block_range(start_height, end_height, self.config.rpc_url)
