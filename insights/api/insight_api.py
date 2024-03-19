import os
import asyncio
from datetime import datetime

import bittensor as bt
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from neurons.validators.utils.uids import get_top_miner_uid
from fastapi import FastAPI, Body
import uvicorn


bt.debug()

def main():
    app = FastAPI()    
    wallet_name = os.getenv("WALLET_NAME")
    wallet_hotkey = os.getenv("WALLET_HOTKEY")
    netuid = os.getenv("NETUID", str(15))
    
    wallet = bt.wallet(name=wallet_name, hotkey=wallet_hotkey)
    
    text_query_api = TextQueryAPI(wallet=wallet)
    
    @app.get("/api/text_query")
    async def get_response(network:str, text: str):
        # select top miner
        metagraph = bt.subtensor("local").metagraph(netuid=netuid)
        top_miner_uid = get_top_miner_uid(metagraph)
        top_miner_axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=top_miner_uid)        
        
        responses=  await text_query_api(
            axons=top_miner_axons,
            network=network,
            input_text=text,
            timeout=40
            )
        
        return responses
            
    @app.get("/")
    def healthcheck():
        return datetime.utcnow()

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", str(2510))))


async def test_query(wallet: "bt.wallet" = None):

    wallet = bt.wallet()

    # Fetch the axons of the available API nodes, or specify UIDs directly
    netuid = os.getenv("NETUID", str(15))
    metagraph = bt.subtensor("local").metagraph(netuid=netuid)
    # Get the best performance miner UIDs
    best_miner_uid = get_top_miner_uid(metagraph)
    axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=best_miner_uid)

    # Change user input
    network = "Bitcoin"
    user_input = "The most recent transaction"

    bt.logging.info(f"Sending {user_input} to get fundflow.")
    fetch_handler = TextQueryAPI(wallet)
    fetch_response = await fetch_handler(
        axons=axons,
        # Arugmnts for the proper synapse
        network=network,
        input_text=user_input,
        timeout=20
    )
    print(fetch_response)


if __name__ == "__main__":
    main()
    
    # Test
    # import asyncio
    # asyncio.run(test_query())