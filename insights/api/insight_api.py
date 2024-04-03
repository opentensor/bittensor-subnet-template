import argparse
import os
import random
import time
import numpy as np

from datetime import datetime

import bittensor as bt
import yaml

from insights import protocol
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body
import uvicorn


bt.debug()

class APIServer:
    def __init__(
            self,
            config: None,
            wallet: None,
            metagraph: None,
        ):
        self.app = FastAPI()
        self.config = config
        self.wallet = wallet
        self.text_query_api = TextQueryAPI(wallet=self.wallet)
        self.metagraph = metagraph
        self.excluded_uids = []
        
        @self.app.get("/api/text_query")
        async def get_response(network:str, text: str):            
            # select top miner            
            top_miner_uids = get_top_miner_uids(self.metagraph, self.config.top_rate, self.excluded_uids)
            bt.logging.info(f"Top miner UIDs are {top_miner_uids}")
            top_miner_axons = await get_query_api_axons(wallet=self.wallet, metagraph=self.metagraph, uids=top_miner_uids)
            bt.logging.info(f"top miner axons: {top_miner_axons}")
            
            # get miner response
            responses, blacklist_axon_ids =  await self.text_query_api(
                axons=top_miner_axons,
                network=network,
                text=text,
                is_generic_llm=False,
                timeout=self.config.timeout
                )
            blacklist_axons = np.array(top_miner_axons)[blacklist_axon_ids]
            blacklist_uids = np.where(np.isin(np.array(self.metagraph.axons), blacklist_axons))[0]
            self.excluded_uids = np.union1d(np.array(self.excluded_uids), blacklist_uids)
            self.excluded_uids = self.excluded_uids.astype(int).tolist()
            
            # If the number of excluded_uids is bigger than top x percentage of the whole axons, format it.
            if len(self.excluded_uids) > int(self.metagraph.n * self.config.top_rate):
                bt.logging.info(f"Excluded UID list is too long")
                self.excluded_uids = []
            bt.logging.info(f"excluded_uids are {self.excluded_uids}")
            bt.logging.info(f"Responses are {responses}")
            if not responses:
                # TODO: I have received 0 responses due to some issues
                return "Please try again. Can't receive any responses due to the poor network connection."
            response = random.choice(responses)
            return response
                
        @self.app.get("/")
        def healthcheck():
            return datetime.utcnow()  
        
    def start(self):
        uvicorn.run(self.app, host="0.0.0.0", port=int(self.config.api_port))
        
