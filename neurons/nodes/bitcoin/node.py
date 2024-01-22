import bittensor as bt
from bitcoinrpc.authproxy import AuthServiceProxy


from neurons.nodes.abstract_node import Node
from neurons.setup_logger import setup_logger

import argparse
import os

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)
logger = setup_logger("BitcoinNode")
 
class BitcoinNode(Node):
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
        except Exception as e:
            logger.error(f"RPC Provider with Error: {e}")
        finally:
            rpc_connection._AuthServiceProxy__conn.close()  # Close the connection
    

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        try:
            block_hash = rpc_connection.getblockhash(block_height)
            return rpc_connection.getblock(block_hash, 2)
        except Exception as e:
            logger.error(f"RPC Provider with Error: {e}")
        finally:
            rpc_connection._AuthServiceProxy__conn.close()  # Close the connection

    def get_transaction_by_hash(self, tx_hash):
        logger.error(f"get_transaction_by_hash not implemented for BitcoinNode")
        raise NotImplementedError()