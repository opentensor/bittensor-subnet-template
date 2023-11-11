from bitcoinrpc.authproxy import AuthServiceProxy
from neurons.miners.configs import BitcoinNodeConfig


class BitcoinNode:
    def __init__(self, config: BitcoinNodeConfig):
        self.config = config

    def is_synced(self):
        rpc_connection = AuthServiceProxy(self.config.node_rpc_url)
        return (
            rpc_connection.getblockcount()
            == rpc_connection.getblockchaininfo()["blocks"]
        )

    def get_current_block_height(self):
        rpc_connection = AuthServiceProxy(self.config.node_rpc_url)
        return rpc_connection.getblockcount()

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.config.node_rpc_url)
        block_hash = rpc_connection.getblockhash(block_height)
        block_data = rpc_connection.getblock(block_hash, 2)
        return block_data

    def get_transactions_from_block_range(self, start_height, end_height):
        all_transactions = []

        for block_height in range(start_height, end_height + 1):
            txs = self.get_transactions_from_block_height(block_height)
            all_transactions.extend((block_height, txs))

        return all_transactions
