import argparse
import asyncio
import json
import traceback
import os
import random
import numpy as np

from datetime import datetime

import bittensor as bt
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body
import uvicorn

from neurons.validators.utils.read_json import is_api_data_valid

bt.debug()

# def get_config():
#     parser = argparse.ArgumentParser()
    
#     parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")
#     parser.add_argument("--port", type=int, default=8001, help="API endpoint port.")
#     parser.add_argument("--timeout", type=int, default=40, help="Timeout.")
#     parser.add_argument("--top_rate", type=float, default=1, help="Best selection percentage")
    
#     bt.subtensor.add_args(parser)
#     bt.logging.add_args(parser)
#     bt.wallet.add_args(parser)
    

#     config = bt.config(parser)
#     return config

excluded_uids = []

def load_api_config():
    bt.logging.debug("Loading API config")

    try:
        if not os.path.exists("neurons/api.json"):
            raise Exception(f"{'neurons/api.json'} does not exist")

        with open("neurons/api.json", 'r') as file:
            api_data = json.load(file)
            bt.logging.trace("api_data", api_data)

            valid, reason = is_api_data_valid(api_data)
            if not valid:
                raise Exception(f"{'neurons/api.json'} is poorly formatted. {reason}")
            if "change-me" in api_data["keys"]:
                bt.logging.warning("YOU ARE USING THE DEFAULT API KEY. CHANGE IT FOR SECURITY REASONS.")
        return api_data
    except Exception as e:
        bt.logging.error("Error loading API config:", e)
        traceback.print_exc()
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
        bt.logging.info(f"excluded_uids are {excluded_uids}")
        bt.logging.info(f"Responses are {responses}")
        if not responses:
            return "This API is banned."
        response = random.choice(responses)
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
        input_text=user_input,
        timeout=config.timeout
    )
    print(fetch_response)


if __name__ == "__main__":
    main()
    