import timeit
import asyncio
import os


from aiohttp import ClientSession

from web3.providers.base import JSONBaseProvider
from web3.providers import HTTPProvider
from web3 import Web3

# asynchronous JSON RPC API request
async def async_make_request(session, url, method, params):
    base_provider = JSONBaseProvider()
    request_data = base_provider.encode_rpc_request(method, params)
    async with session.post(url, data=request_data,
                        headers={'Content-Type': 'application/json'}) as response:
        content = await response.read()
    response = base_provider.decode_rpc_response(content)
    print(f"{response}")
    return response

async def run_get_transaction(node_address, transactions):
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        for tran in transactions:
            task = asyncio.ensure_future(async_make_request(session, node_address,
                                                            'eth_getTransactionReceipt',[tran.hex()]))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

def get_transactions_from_hash(eth_node_address, transactions):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run_get_transaction(eth_node_address, transactions))
    loop.run_until_complete(future)
    