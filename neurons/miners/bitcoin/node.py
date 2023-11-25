import argparse
import itertools
import os
import sys
from _decimal import Decimal

import bittensor as bt
from datetime import time
from bitcoinrpc.authproxy import AuthServiceProxy

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)

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

    def get_current_block_height(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        return rpc_connection.getblockcount()

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        block_hash = rpc_connection.getblockhash(block_height)
        block_data = rpc_connection.getblock(block_hash, 2)
        return block_data

    def sum_vout_values(self, block):
        SATOSHI = Decimal("100000000")
        total_value = 0
        value_satoshi = 0
        for transaction in block["tx"]:
            for vout in transaction["vout"]:
                total_value += vout['value']
                value_satoshi += int(Decimal(vout["value"]) * SATOSHI)

        return total_value

    def sum_vout_values_count(self, block):
        SATOSHI = Decimal("100000000")
        total_value_count = 0

        for transaction in block["tx"]:
            for vout in transaction["vout"]:
                total_value_count += 1

        return total_value_count

