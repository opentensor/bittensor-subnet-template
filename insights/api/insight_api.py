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

excluded_uids = []
class APIServer:
    app: FastAPI
    wallet: bt.wallet
    subtensor: bt.subtensor
    text_query_api: TextQueryAPI
    
    def __init__(
            self,
            config
    ):
        self.app = FastAPI()
        self.config = config
        self.wallet = bt.wallet(config=self.config)
        self.subtensor = bt.subtensor(config=self.config)
        self.text_query_api = TextQueryAPI(wallet=self.wallet)
        
        @self.app.get("/api/text_query")
        async def get_response(network:str, text: str):
            global excluded_uids
            # select top miner
            metagraph = self.subtensor.metagraph(self.config.netuid) # sync every request
            top_miner_uids = get_top_miner_uids(metagraph, self.config.top_rate, excluded_uids)
            bt.logging.info(f"Top miner UIDs are {top_miner_uids}")
            top_miner_axons = await get_query_api_axons(wallet=self.wallet, metagraph=metagraph, uids=top_miner_uids)
            bt.logging.info(f"top miner axons: {top_miner_axons}")
            
            # get miner response
            responses, blacklist_axon_ids =  await self.text_query_api(
                axons=top_miner_axons,
                network=network,
                text=text,
                timeout=self.config.timeout
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
                
        @self.app.get("/")
        def healthcheck():
            return datetime.utcnow()  
        
    def start(self):
        uvicorn.run(self.app, host="0.0.0.0", port=int(self.config.api_port))
        
