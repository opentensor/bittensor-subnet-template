import argparse
import asyncio
import os
import random
import time
import numpy as np

from datetime import datetime

import protocol
import bittensor as bt
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body
import uvicorn

bt.debug()

def get_config():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
    parser.add_argument("--port", type=int, default=8001, help="API endpoint port.")
    parser.add_argument("--timeout", type=int, default=40, help="Timeout.")
    parser.add_argument("--top_rate", type=float, default=1, help="Best selection percentage")
    
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)
    

    config = bt.config(parser)
    return config

def handle_llm_interpret_error(errorcode: protocol.ERROR_TYPE):
    if errorcode == protocol.LLM_ERROR_TYPE_NOT_SUPPORTED:
        return "This Query is not allowed"
    elif errorcode == protocol.LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED:
        # Todo
        return "There's not required type"
    else:
        return "Can't handle this query"
    

excluded_uids = []
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
    bt.logging.info(f"Top_rate: {config.top_rate}")
    
    text_query_api = TextQueryAPI(wallet=wallet)
    
    @app.get("/api/text_query")
    async def get_response(network:str, text: str):
        global excluded_uids
        
        # select top miner
        metagraph = subtensor.metagraph(config.netuid) # sync every request
        top_miner_uids = get_top_miner_uids(metagraph, config.top_rate, excluded_uids)
        bt.logging.info(f"Top miner UIDs are {top_miner_uids}")
        top_miner_axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=top_miner_uids)
        bt.logging.info(f"top miner axons: {top_miner_axons}")
        
        # get miner response
        responses, blacklist_axon_ids =  await text_query_api(
            axons=top_miner_axons,
            network=network,
            text=text,
            timeout=config.timeout
            )
        blacklist_axons = np.array(top_miner_axons)[blacklist_axon_ids]
        blacklist_uids = np.where(np.isin(np.array(metagraph.axons), blacklist_axons))[0]
        excluded_uids = np.union1d(np.array(excluded_uids), blacklist_uids)
        excluded_uids = excluded_uids.astype(int).tolist()
        
        # If the number of excluded_uids is bigger than top x percentage of the whole axons, format it.
        if len(excluded_uids) > int(metagraph.n * config.top_rate):
            bt.logging.info(f"Excluded UID list is too long")
            excluded_uids = []
        bt.logging.info(f"excluded_uids are {excluded_uids}")
        bt.logging.info(f"Responses are {responses}")
        
        if not responses:
            return "This hotkey is banned."
        response = random.choice(responses)
        if response.error != protocol.LLM_ERROR_NO_ERROR:
            return handle_llm_interpret_error(response.error)
        return response
            
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
    bt.logging.info(f"Top_rate: {config.top_rate}")
    # Get the top miner UIDs
    top_miner_uids = get_top_miner_uids(metagraph, config.top_rate)
    axons = await get_query_api_axons(wallet=wallet, metagraph=metagraph, uids=top_miner_uids)

    # Change user input
    network = "Bitcoin"
    user_input = "The most recent transaction"

    bt.logging.info(f"Sending {user_input} to get fundflow.")
    fetch_handler = TextQueryAPI(wallet)
    fetch_response = await fetch_handler(
        axons=axons,
        # Arugmnts for the proper synapse
        network=network,
        text=user_input,
        timeout=config.timeout
    )
    print(fetch_response)


if __name__ == "__main__":
    main()
    
    # Test
    # import asyncio
    # asyncio.run(test_query())