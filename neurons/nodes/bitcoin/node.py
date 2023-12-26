import argparse
import os

import bittensor as bt
from bitcoinrpc.authproxy import AuthServiceProxy

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)

class BitcoinNode:
    def __init__(self, node_rpc_url: str = None):
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("BITCOIN_NODE_RPC_URL")
                or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
            )
        else:
            self.node_rpc_url = node_rpc_url

    def get_current_block_height(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        try:
            return rpc_connection.getblockcount()
        finally:
            rpc_connection._AuthServiceProxy__conn.close()  # Close the connection

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        try:
            block_hash = rpc_connection.getblockhash(block_height)
            return rpc_connection.getblock(block_hash, 2)
        finally:
            rpc_connection._AuthServiceProxy__conn.close()  # Close the connection
