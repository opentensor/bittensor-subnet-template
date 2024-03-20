import argparse
import asyncio
import os

from datetime import datetime

import bittensor as bt
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from neurons.validators.utils.uids import get_top_miner_uid
from fastapi import FastAPI, Body
import uvicorn


bt.debug()

def get_config():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
    parser.add_argument("--port", type=int, default=8001, help="API endpoint port.")
    parser.add_argument("--timeout", type=int, default=40, help="Timeout.")
    
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)
    

    config = bt.config(parser)
    return config

def main():
    app = FastAPI()
    config = get_config()    
    wallet = bt.wallet(config=config)
    subtensor = bt.subtensor(config=config)
    metagraph = subtensor.metagraph(config.netuid)

    bt.logging.info(f"Wallet: {wallet}")
    bt.logging.info(f"Subtensor: {subtensor}")
    bt.logging.info(f"Metagraph: {metagraph}")
    bt.logging.info(f"Port: {config.port}")
    bt.logging.info(f"Timeout: {config.timeout}")
    
    text_query_api = TextQueryAPI(wallet=wallet)
    
    @app.get("/api/text_query")
    async def get_response(network:str, text: str):
        # select top miner
        metagraph = subtensor.metagraph(netuid=config.netuid)
        top_miner_uid = get_top_miner_uid(metagraph)
        bt.logging.info(f"Top miner UID is {top_miner_uid}")        
        top_miner_axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=top_miner_uid)        
        # get miner response
        responses=  await text_query_api(
            axons=top_miner_axons,
            network=network,
            input_text=text,
            timeout=config.timeout
            )
        
        return responses
            
    @app.get("/")
    def healthcheck():
        return datetime.utcnow()
    
    uvicorn.run(app, host="0.0.0.0", port=int(config.port))


async def test_query(wallet: "bt.wallet" = None):

    config = get_config()
    
    wallet = bt.wallet(config=config)
    subtensor = bt.subtensor(config=config)
    metagraph = subtensor.metagraph(config.netuid)
    

    bt.logging.info(f"Wallet: {wallet}")
    bt.logging.info(f"Subtensor: {subtensor}")
    bt.logging.info(f"Metagraph: {metagraph}")
    bt.logging.info(f"Port: {config.port}")
    bt.logging.info(f"Timeout: {config.timeout}")
    # Get the top miner UIDs
    top_miner_uid = get_top_miner_uid(metagraph)
    axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=top_miner_uid)

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
        timeout=config.timeout
    )
    print(fetch_response)


if __name__ == "__main__":
    main()
    
    # Test
    # import asyncio
    # asyncio.run(test_query())