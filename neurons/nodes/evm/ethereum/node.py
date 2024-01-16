import argparse
import asyncio
import os

from aiohttp import ClientSession

import bittensor as bt
from web3 import Web3
from neurons.setup_logger import setup_logger
from neurons.nodes.evm.ethereum.node_utils import async_rpc_request

parser = argparse.ArgumentParser()
bt.logging.add_args(parser)
logger = setup_logger("EvmNode")
 
class EthereumNode:
    def __init__(self, node_rpc_url: str = None):
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("ETHEREUM_NODE_RPC_URL")
                or "http://ethereumrpc:rpcpassword@127.0.0.1:8545"
            )
        else:
            self.node_rpc_url = node_rpc_url

    def get_current_block_height(self):
        web3 = Web3(Web3.HTTPProvider(self.node_rpc_url))
        try:
            if web3.is_connected:
                return web3.eth.block_number
            else:
                logger.info("RPC Provider disconnected.")
        except Exception as e:
            logger.error(f"RPC Provider with Error: {e}")
        finally:
            web3.provider = None # Close the connection
    
    def get_block_by_height(self, block_height):
        web3 = Web3(Web3.HTTPProvider(self.node_rpc_url))
        try:
            if web3.is_connected:
                return web3.eth.get_block(block_height)
            else:
                logger.info("RPC Provider disconnected.")
        except Exception as e:
            logger.error(f"RPC Provider with Error: {e}")
        finally:
            web3.provider = None # Close the connection

    def get_transaction_by_hash(self, tx_hash): # get the transaction details from tx hash
        web3 = Web3(Web3.HTTPProvider(self.node_rpc_url))
        try:
            if web3.is_connected:
                return web3.eth.get_transaction(tx_hash)
            else:
                logger.info(f("RPC Provider disconnected."))
        except Exception as e:
            logger.error(f"RPC Provider with Error: {e}")
        finally:
            web3.provider = None # Close the connection
    
    async def get_balance_by_addresses(self, addresses): # get the balance from addresses
        tasks = []
        # Fetch all responses within one Client session,
        # keep connection alive for all requests.
        async with ClientSession() as session:
            for address in addresses:
                task = async_rpc_request(session, self.node_rpc_url, 'eth_getBalance', [address, 'pending'])
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            return responses

    async def get_transaction(self, transactions): # get tx details from tx hash
        try:
            tasks = []
            # Fetch all responses within one Client session,
            # keep connection alive for all requests.
            async with ClientSession() as session:
                for tran in transactions:
                    task = async_rpc_request(session, self.node_rpc_url, 'eth_getTransactionByHash',[tran.hex()])
                    tasks.append(task)

                responses = await asyncio.gather(*tasks)
                return responses
        except Exception as e:
            logger.error(f"RPC Provider with Error: {e}")