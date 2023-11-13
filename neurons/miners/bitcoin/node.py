import itertools
import os
import sys
from datetime import time
from bitcoinrpc.authproxy import AuthServiceProxy


class BitcoinNode:
    def __init__(self, node_rpc_url: str = None):
        """
        Args:
            node_rpc_url:
        """
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("NODE_RPC_URL")
                or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
            )
        else:
            self.node_rpc_url = node_rpc_url

    def is_synced(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        return (
            rpc_connection.getblockcount()
            == rpc_connection.getblockchaininfo()["blocks"]
        )

    def get_current_block_height(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        return rpc_connection.getblockcount()

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        block_hash = rpc_connection.getblockhash(block_height)
        block_data = rpc_connection.getblock(block_hash, 2)
        return block_data

    def spinner(self):
        spinner_words = itertools.cycle(["Tao", "Bit", "Tensor", "AI"])
        while True:
            yield next(spinner_words)

    def is_synced(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        spinner_gen = self.spinner()
        try:
            while True:
                current_block = rpc_connection.getblockcount()
                highest_block = rpc_connection.getblockchaininfo()["blocks"]
                spinner_word = next(spinner_gen)
                sys.stdout.write(
                    f"\rChecking sync status... {spinner_word} {current_block}/{highest_block}"
                )
                sys.stdout.flush()

                # Check if the current block is equal to the highest block
                if current_block == highest_block:
                    sys.stdout.write("\nNode is synced!\n")
                    return True
                else:
                    time.sleep(1)  # Wait a bit before checking again
        except Exception as e:
            sys.stdout.write(f"\nFailed to check sync status: {e}\n")
            return False
