# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2023 Opentensor Technologies Inc

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


import bittensor as bt
from template.api import DummyAPI, get_query_api_axons
bt.debug()

# Example usage
async def test_dummy():

    wallet = bt.wallet()

    store_handler = DummyAPI(wallet)

    # Fetch the axons of the available API nodes, or specify UIDs directly
    metagraph = bt.subtensor("test").metagraph(netuid=22)
    axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=[5, 7])

    # Store some data!
    raw_data = b"Hello FileTao!"

    bt.logging.info(f"Storing data {raw_data} on the Bittensor testnet.")
    cid = await store_handler(
        axons=axons,
        # any arguments for the proper synapse
        data=raw_data,
        encrypt=False, # optionally encrypt the data with your bittensor wallet
        ttl=60 * 60 * 24 * 30,
        encoding="utf-8",
        uid=None,
        timeout=60,
    )

    print(retrieve_response)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_storage())