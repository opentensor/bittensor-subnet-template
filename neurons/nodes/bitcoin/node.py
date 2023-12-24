import argparse
import time
import bittensor as bt
import os
import queue
from bitcoinrpc.authproxy import AuthServiceProxy

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)

class BitcoinNode:
    _instance = None
    _connection_pool = None
    _pool_size = 64

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BitcoinNode, cls).__new__(cls)
            cls._instance._initialize_connection_pool()
        return cls._instance

    def _initialize_connection_pool(self):
        self._connection_pool = queue.Queue(maxsize=self._pool_size)
        for _ in range(self._pool_size):
            rpc_url = os.environ.get("BITCOIN_NODE_RPC_URL") or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
            self._connection_pool.put(AuthServiceProxy(rpc_url))

    def _get_rpc_connection(self):
        return self._connection_pool.get()

    def _return_rpc_connection(self, connection):
        self._connection_pool.put(connection)

    def _attempt_rpc_call(self, rpc_method, *args, max_retries=8):
        for attempt in range(max_retries):
            rpc_connection = self._get_rpc_connection()
            try:
                return rpc_method(rpc_connection, *args)
            except Exception as e:
                bt.logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise  # Re-raise the last exception if all attempts fail
                time.sleep(8)
            finally:
                self._return_rpc_connection(rpc_connection)

    def get_current_block_height(self):
        def rpc_call(rpc_connection):
            return rpc_connection.getblockcount()

        return self._attempt_rpc_call(rpc_call)

    def get_block_by_height(self, block_height):
        def rpc_call(rpc_connection, block_height):
            block_hash = rpc_connection.getblockhash(block_height)
            return rpc_connection.getblock(block_hash, 2)

        return self._attempt_rpc_call(rpc_call, block_height)
