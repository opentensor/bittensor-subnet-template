import argparse
import os

import bittensor as bt
from bitcoinrpc.authproxy import AuthServiceProxy

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)

class BitcoinNode:
    _instance = None
    _rpc_connection = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BitcoinNode, cls).__new__(cls)
        return cls._instance

    def __init__(self, node_rpc_url: str = None):
        if self._rpc_connection is None:
            if node_rpc_url is None:
                node_rpc_url = (
                    os.environ.get("BITCOIN_NODE_RPC_URL")
                    or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
                )
            self._rpc_connection = AuthServiceProxy(node_rpc_url)

    def get_current_block_height(self):
        return self._rpc_connection.getblockcount()

    def get_block_by_height(self, block_height):
        block_hash = self._rpc_connection.getblockhash(block_height)
        block_data = self._rpc_connection.getblock(block_hash, 2)
        return block_data
