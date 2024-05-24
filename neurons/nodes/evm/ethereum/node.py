import argparse
import os
from Crypto.Hash import SHA256
from insights.protocol import Challenge
import random

import requests

import bittensor as bt
from web3 import Web3
from web3.providers.base import JSONBaseProvider
from neurons.nodes.abstract_node import Node
from neurons.setup_logger import setup_logger

parser = argparse.ArgumentParser()
from neurons import logger
bt.logging.add_args(parser)
indexlogger = setup_logger("EvmNode")
 
class EthereumNode(Node):
    def __init__(self, node_rpc_url: str = None):
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("ETHEREUM_NODE_RPC_URL")
                or "http://ethereumrpc:rpcpassword@127.0.0.1:8545"
            )
        else:
            self.node_rpc_url = node_rpc_url
        
        self.web3 = Web3(Web3.HTTPProvider(self.node_rpc_url))

    def close_provider(self):
        self.web3.provider = None

    def get_current_block_height(self):
        try:
            if self.web3.is_connected:
                return self.web3.eth.block_number
            else:
                indexlogger.info("RPC Provider disconnected.")
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})
    
    def get_block_by_height(self, block_height):
        try:
            if self.web3.is_connected:
                return self.web3.eth.get_block(block_height)
            else:
                indexlogger.info("RPC Provider disconnected.")
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})

    def get_transaction_by_hash(self, tx_hash): # get the transaction details from tx hash
        try:
            if self.web3.is_connected:
                return self.web3.eth.get_transaction(tx_hash)
            else:
                indexlogger.info(f("RPC Provider disconnected."))
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})
    
    def get_symbol_name(self, contractAddress):
        jsonAbi = [{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"}]
        try:
            if self.web3.is_connected:
                contract = self.web3.eth.contract(address=contractAddress, abi=jsonAbi)
                return contract.functions.symbol().call()
            else:
                indexlogger.info(f("RPC Provider disconnected."))
        except:
            return contractAddress
    
    # get the balance from addresses
    def get_balance_by_addresses(self, addresses):
        try:
            batch_size = 500
            sub_arrays = [addresses[i:i + batch_size] for i in range(0, len(addresses), batch_size)]
            responses = []

            for addrs in sub_arrays:
                base_provider = JSONBaseProvider()
                request_data = b'[' + b','.join([base_provider.encode_rpc_request('eth_getBalance', [addr, 'latest']) for addr in addrs]) + b']'
                r = requests.post(self.node_rpc_url, data=request_data, headers={'Content-Type': 'application/json'})
                responses += base_provider.decode_rpc_response(r.content)

            return responses
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})

    # get tx details from tx hash
    def get_transaction(self, transactions):
        try:
            batch_size = 500
            sub_arrays = [transactions[i:i + batch_size] for i in range(0, len(transactions), batch_size)]
            responses = []

            for txs in sub_arrays:
                base_provider = JSONBaseProvider()
                request_data = b'[' + b','.join([base_provider.encode_rpc_request('eth_getTransactionByHash', [tran]) for tran in txs]) + b']'
                r = requests.post(self.node_rpc_url, data=request_data, headers={'Content-Type': 'application/json'})
                responses += base_provider.decode_rpc_response(r.content)

            return responses
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})

    # get txReceipt details from tx hash
    def get_transactionReceipt(self, transactions):
        try:
            batch_size = 500
            sub_arrays = [transactions[i:i + batch_size] for i in range(0, len(transactions), batch_size)]
            responses = []

            for txs in sub_arrays:
                base_provider = JSONBaseProvider()
                request_data = b'[' + b','.join([base_provider.encode_rpc_request('eth_getTransactionReceipt', [tran]) for tran in txs]) + b']'
                r = requests.post(self.node_rpc_url, data=request_data, headers={'Content-Type': 'application/json'})
                responses += base_provider.decode_rpc_response(r.content)

            return responses
        except Exception as e:
            indexlogger.error(f"RPC Provider with Error", error = {'exception_type': e.__class__.__name__,'exception_message': str(e),'exception_args': e.args})

    def create_challenge(self, start_block_height, last_block_height):
        block_to_check = random.randint(start_block_height, last_block_height)
        
        block_data = self.get_block_by_height(block_to_check)
        num_transactions = len(block_data["tx"])

        out_total_amount = 0
        while out_total_amount == 0:
            selected_txn = block_data["tx"][random.randint(0, num_transactions - 1)]
            txn_id = selected_txn.get('hash')

            binary = selected_txn["hash"] + selected_txn["blockHash"] + selected_txn["from"] + selected_txn["to"]
            checksum = SHA256.new(binary.encode('utf-8')).hexdigest()

        challenge = Challenge(checksum=checksum)
        return challenge, txn_id
