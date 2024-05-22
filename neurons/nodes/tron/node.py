import argparse
import os
from Crypto.Hash import SHA256
from insights.protocol import Challenge
import random

import bittensor as bt
from tronapi import Tron
from neurons.nodes.abstract_node import Node
from neurons.setup_logger import setup_logger

parser = argparse.ArgumentParser()
from neurons import logger
bt.logging.add_args(parser)
indexlogger = setup_logger("TronNode")
 
class TronNode(Node):
    def __init__(self, node_rpc_url: str = None):
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("TRON_NODE_RPC_URL")
                or "http://tronrpc:rpcpassword@127.0.0.1:50051"
            )
        else:
            self.node_rpc_url = node_rpc_url
        
        self.tron = Tron(full_node=self.node_rpc_url,
        solidity_node=self.node_rpc_url,
        event_server=self.node_rpc_url)

    def get_current_block_height(self):
        try:
            if self.tron.is_connected:
                block_header = self.tron.trx.get_current_block()
                return block_header['block_header']['raw_data']['number']
            else:
                indexlogger.info("RPC Provider disconnected.")
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")
    
    def get_block_by_height(self, block_height):
        try:
            if self.tron.is_connected:
                return self.tron.trx.get_block(block_height)
            else:
                indexlogger.info("RPC Provider disconnected.")
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")

    def get_transaction_by_hash(self, tx_hash): # get the transaction details from tx hash
        try:
            if self.tron.is_connected:
                return self.tron.trx.get_transaction(tx_hash)
            else:
                indexlogger.info(f("RPC Provider disconnected."))
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")
    
    def get_transaction_info(self, tx_hash): # get the transaction details from tx hash
        try:
            if self.tron.is_connected:
                return self.tron.trx.get_transaction_info(tx_hash)
            else:
                indexlogger.info(f("RPC Provider disconnected."))
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")

    def get_account_balance(self, address): # get account balance in sun
        try:
            if self.tron.is_connected:
                return self.tron.trx.get_balance(address)
            else:
                indexlogger.info(f("RPC Provider disconnected."))
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")

    # get the balance from addresses - batch request
    def get_balance_by_addresses(self, addresses):
        try:
            responses = []
            for address in addresses:
                responses.append(self.get_account_balance(address))

            return responses
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")

    # get tx details from tx hash - batch request
    def get_transaction(self, transactions):
        try:
            responses = []
            for tx in transactions:
                responses.append(self.get_transaction_by_hash(tx))

            return responses
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")

    # get txReceipt details from tx hash - batch request
    def get_transactionReceipt(self, transactions):
        try:
            responses = []
            for tx in transactions:
                responses.append(self.get_transaction_info(tx))

            return responses
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error: {e}")

    def create_challenge(self, start_block_height, last_block_height):
        block_to_check = random.randint(start_block_height, last_block_height)
        
        block_data = self.get_block_by_height(block_to_check)
        num_transactions = len(block_data["transactions"])

        out_total_amount = 0
        while out_total_amount == 0:
            selected_txn = block_data["transactions"][random.randint(0, num_transactions - 1)]
            txn_id = selected_txn.get('txID')

            accountInfo = selected_txn["raw_data"]["contract"][0]["parameter"]
            from_address = self.tron.address.from_hex(accountInfo["owner_address"])
            to_address = self.tron.address.from_hex(accountInfo["to_address"])
            binary = selected_txn["txID"] + selected_txn["blockID"] + from_address.decode('utf-8') + to_address.decode('utf-8')
            checksum = SHA256.new(binary.encode('utf-8')).hexdigest()

        challenge = Challenge(checksum=checksum)
        return challenge, txn_id