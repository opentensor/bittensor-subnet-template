import argparse
import os

import bittensor as bt
from bitcoinrpc.authproxy import AuthServiceProxy

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)


class DogecoinNode:
    def __init__(self, node_rpc_url: str = None):
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("DOGE_NODE_RPC_URL")
                or "http://doge:doge@127.0.0.1:44555"
            )
        else:
            self.node_rpc_url = node_rpc_url

    def get_current_block_height(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        return rpc_connection.getblockcount()

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        block_hash = rpc_connection.getblockhash(block_height)
        block_data = rpc_connection.getblock(block_hash, True)

        full_transactions = []
        for txid in block_data["tx"]:
            raw_tx = rpc_connection.getrawtransaction(txid)
            decoded_tx = rpc_connection.decoderawtransaction(raw_tx)
            full_transactions.append(decoded_tx)

        # Construct the final structure similar to Bitcoin's verbose getblock output
        block_data["tx"] = full_transactions

        # bt.logging.info("Block data: {}".format(block_data))
        return block_data
