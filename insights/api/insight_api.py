import argparse
import os
import random
import time
import numpy as np
from typing import List, Optional, Union, Any, Dict
from datetime import datetime
import traceback
import torch
import bittensor as bt
import yaml

from insights import protocol
from insights.protocol import QueryOutput
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from insights.api.schema.chat import ChatMessageRequest, ChatMessageResponse, ChatMessageVariantRequest
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body
import uvicorn


bt.debug()

class APIServer:
    def is_response_status_code_valid(self, response):
            status_code = response.axon.status_code
            status_message = response.axon.status_message
            if response.is_failure:
                bt.logging.info(f"Discovery response: Failure, miner {response.axon.hotkey} returned {status_code=}: {status_message=}")
            elif response.is_blacklist:
                bt.logging.info(f"Discovery response: Blacklist, miner {response.axon.hotkey} returned {status_code=}: {status_message=}")
            elif response.is_timeout:
                bt.logging.info(f"Discovery response: Timeout, miner {response.axon.hotkey}")
            return status_code == 200
        
    def get_reward(self, response: Union["bt.Synapse", Any], uid: int):
        return 0.5
        
    def update_scores(self, rewards: torch.FloatTensor, uids: List[int]):
        """Performs exponential moving average on the scores based on the rewards received from the miners."""

        # Check if rewards contains NaN values.
        if torch.isnan(rewards).any():
            bt.logging.warning(f"NaN values detected in rewards: {rewards}")
            # Replace any NaN values in rewards with 0.
            rewards = torch.nan_to_num(rewards, 0)

        # Check if `uids` is already a tensor and clone it to avoid the warning.
        if isinstance(uids, torch.Tensor):
            uids_tensor = uids.clone().detach()
        else:
            uids_tensor = torch.tensor(uids).to(self.device)

        # Compute forward pass rewards, assumes uids are mutually exclusive.
        # shape: [ metagraph.n ]
        scattered_rewards: torch.FloatTensor = self.scores.scatter(
            0, uids_tensor, rewards
        ).to(self.device)
        bt.logging.debug(f"Scattered rewards: {rewards}")

        # Update scores with rewards produced by this step.
        # shape: [ metagraph.n ]
        alpha: float = self.config.user_query_moving_average_alpha
        self.scores: torch.FloatTensor = alpha * scattered_rewards + (
            1 - alpha
        ) * self.scores.to(self.device)
        bt.logging.debug(f"Updated moving avg scores: {self.scores}")
        
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
                timeout=self.config.timeout
                )
            
            # Update exlucded_uids
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
        
        @self.app.post("/api/text_query")
        async def get_response(query: ChatMessageRequest = Body(...)):
            # select top miner            
            top_miner_uids = get_top_miner_uids(self.metagraph, self.config.top_rate, self.excluded_uids)
            bt.logging.info(f"Top miner UIDs are {top_miner_uids}")
            top_miner_axons = await get_query_api_axons(wallet=self.wallet, metagraph=self.metagraph, uids=top_miner_uids)
            bt.logging.info(f"Top miner axons: {top_miner_axons}")
            
            # get miner response
            responses, blacklist_axon_ids =  await self.text_query_api(
                axons=top_miner_axons,
                network=query.network,
                text=query.prompt,
                timeout=self.config.timeout
            )
            
            if not responses:
                # TODO: I have received 0 responses due to some issues
                return "Please try again. Can't receive any responses due to the poor network connection."
            
            blacklist_axons = np.array(top_miner_axons)[blacklist_axon_ids]
            blacklist_uids = np.where(np.isin(np.array(self.metagraph.axons), blacklist_axons))[0]
            # get responded miner uids among top miners
            responded_uids = np.setdiff1d(np.array(top_miner_uids), blacklist_uids)
            self.excluded_uids = np.union1d(np.array(self.excluded_uids), blacklist_uids)
            self.excluded_uids = self.excluded_uids.astype(int).tolist()

            # Add score to miners respond to user query
            uids = responded_uids.tolist()
            rewards = [
                self.get_reward(response, uid) for response, uid in zip(responses, uids)
            ]
            # Remove None reward as they represent timeout cross validation
            filtered_data = [(reward, uid) for reward, uid in zip(rewards, uids) if reward is not None]

            if filtered_data:
                rewards, uids = zip(*filtered_data)

                rewards = torch.FloatTensor(rewards)
                self.update_scores(rewards, uids)
            else:  
                bt.logging.info('Skipping update_scores() as no responses were valid')

            # If the number of excluded_uids is bigger than top x percentage of the whole axons, format it.
            if len(self.excluded_uids) > int(self.metagraph.n * self.config.top_rate):
                bt.logging.info(f"Excluded UID list is too long")
                self.excluded_uids = []            
            bt.logging.info(f"Excluded_uids are {self.excluded_uids}")

            bt.logging.info(f"Responses are {responses}")
            
            selected = random.choice(len(responses))

            # return response and the hotkey of randomly selected miner
            return ChatMessageResponse(text=responses[selected], miner_id=self.metagraph.hotkeys[responded_uids[selected]])
        
        @self.app.post("api/text_query/variant")
        async def get_response_variant(query: ChatMessageVariantRequest = Body(...)):
            bt.logging.info(f"Miner {query.miner_id} received a variant request.")
            
            miner_axon = await get_query_api_axons(wallet=self.wallet, metagraph=self.metagraph, uids=query.miner_id)
            bt.logging.info(f"Miner axon: {miner_axon}")
            
            responses, blacklist_axon_ids =  await self.text_query_api(
                axons=miner_axon,
                network=query.network,
                text=query.prompt,
                timeout=self.config.timeout
            )
            
            if not responses:
                # TODO: I have received 0 responses due to some issues
                return "Please try again. Can't receive any responses due to the poor network connection."
            
            bt.logging.info(f"Variant: {responses}")

            # return response and the hotkey of randomly selected miner
            return ChatMessageResponse(text=responses[0], miner_id=query.miner_id)
                
        @self.app.get("/")
        def healthcheck():
            return datetime.utcnow()  
        
    def start(self):
        uvicorn.run(self.app, host="0.0.0.0", port=int(self.config.api_port))
        
