import timeit
import asyncio
import os


from aiohttp import ClientSession

from web3.providers.base import JSONBaseProvider
from web3.providers import HTTPProvider
from web3 import Web3

# synchronously request receipts for given transactions
def sync_receipts(web3, transactions):
    for tran in transactions:
        web3.eth.get_transaction(tran)

# asynchronous JSON RPC API request
async def async_make_request(session, url, method, params):
    base_provider = JSONBaseProvider()
    request_data = base_provider.encode_rpc_request(method, params)
    async with session.post(url, data=request_data,
                        headers={'Content-Type': 'application/json'}) as response:
        content = await response.read()
    response = base_provider.decode_rpc_response(content)
    return response

async def run(node_address, transactions):
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        for tran in transactions:
            # task = asyncio.ensure_future(async_make_request(session, node_address, 'eth_getTransactionByHash',[tran.hex()]))
            task = async_make_request(session, node_address, 'eth_getTransactionByHash',[tran.hex()])
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return responses

async def balanceRun(node_address, addresses):
        tasks = []
        # Fetch all responses within one Client session,
        # keep connection alive for all requests.
        async with ClientSession() as session:
            for address in addresses:
                task = async_make_request(session, node_address, 'eth_getBalance', [address, 'pending'])
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            return responses


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    eth_node_address = os.environ.get("ETHEREUM_NODE_RPC_URL")
    web3 = Web3(HTTPProvider(eth_node_address))

    block = web3.eth.get_block(18639982)
    transactions = block['transactions']
    start_time = timeit.default_timer()
    sync_receipts(web3, transactions)
    print('sync: {:.3f}s'.format(timeit.default_timer() - start_time))

    start_time = timeit.default_timer()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(eth_node_address, transactions))
    # future = balanceRun(eth_node_address, ['0x98c3d3183c4b8a650614ad179a1a98be0a8d6b8e', '0x3f22f60936f4f5d1e96cedeb44bee66d0cd7c220'])
    result = loop.run_until_complete(future)
    print('async: {:.3f}s'.format(timeit.default_timer() - start_time))
    print(f"{result}")