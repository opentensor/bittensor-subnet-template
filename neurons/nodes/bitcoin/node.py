import bittensor as bt
from bitcoinrpc.authproxy import AuthServiceProxy


from neurons.nodes.abstract_node import Node
from neurons.nodes.bitcoin.node_utils import (
    pubkey_to_address,
    construct_redeem_script,
    hash_redeem_script,
    create_p2sh_address,
)
from neurons.setup_logger import setup_logger

from .node_utils import initialize_tx_out_hash_table, get_tx_out_hash_table_sub_keys

import argparse
import pickle
import time
import os

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)
logger = setup_logger("BitcoinNode")
 
class BitcoinNode(Node):
    def __init__(self, node_rpc_url: str = None):
        self.tx_out_hash_table = initialize_tx_out_hash_table()
        pickle_files = os.environ.get("BITCOIN_TX_OUT_HASHMAP_PICKLES")
        if pickle_files:
            for pickle_file in pickle_files.split(','):
                if os.path.exists(pickle_file):
                    self.load_tx_out_hash_table(pickle_file)
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("BITCOIN_NODE_RPC_URL")
                or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
            )
        else:
            self.node_rpc_url = node_rpc_url

    def load_tx_out_hash_table(self, pickle_path: str, reset: bool = False):
        logger.info(f"Loading tx_out hash table: {pickle_path}")
        with open(pickle_path, 'rb') as file:
            start_time = time.time()
            hash_table = pickle.load(file)
            if reset:
                self.tx_out_hash_table = hash_table
            else:
                sub_keys = get_tx_out_hash_table_sub_keys()
                for sub_key in sub_keys:
                    self.tx_out_hash_table[sub_key].update(hash_table[sub_key])
            end_time = time.time()
            logger.info(f"Successfully loaded tx_out hash table: {pickle_path} in {end_time - start_time} seconds")

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
    
    def get_address_and_amount_by_txn_id_and_vout_id(self, txn_id: str, vout_id: str):
        # call rpc if not in hash table
        if (txn_id, vout_id) not in self.tx_out_hash_table[txn_id[:3]]:
            # logger.info(f"No entry is found in tx_out hash table: (tx_id, vout_id): ({txn_id}, {vout_id})")
            rpc_connection = AuthServiceProxy(self.node_rpc_url)
            try:
                txn_data = rpc_connection.getrawtransaction(str(txn_id), 1)
                vout = next((x for x in txn_data['vout'] if str(x['n']) == vout_id), None)
                amount = int(vout['value'] * 100000000)
                address = vout["scriptPubKey"].get("address", "")
                script_pub_key_asm = vout["scriptPubKey"].get("asm", "")
                if not address:
                    addresses = vout["scriptPubKey"].get("addresses", [])
                    if addresses:
                        address = addresses[0]
                    elif "OP_CHECKSIG" in script_pub_key_asm:
                        pubkey = script_pub_key_asm.split()[0]
                        address = pubkey_to_address(pubkey)
                    elif "OP_CHECKMULTISIG" in script_pub_key_asm:
                        pubkeys = script_pub_key_asm.split()[1:-2]
                        m = int(script_pub_key_asm.split()[0])
                        redeem_script = construct_redeem_script(pubkeys, m)
                        hashed_script = hash_redeem_script(redeem_script)
                        address = create_p2sh_address(hashed_script)
                    else:
                        raise Exception(
                            f"Unknown address type: {vout['scriptPubKey']}"
                        )
                return address, amount
            finally:
                rpc_connection._AuthServiceProxy__conn.close()  # Close the connection
        else: # get from hash table if exists
            address, amount = self.tx_out_hash_table[txn_id[:3]][(txn_id, vout_id)]
            return address, int(amount)
