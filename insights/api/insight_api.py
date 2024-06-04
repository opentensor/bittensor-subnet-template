import os
import random
import asyncio
import json
from datetime import datetime
import traceback
import bittensor as bt
from rich.table import Table
from rich.console import Console
import yaml

import numpy as np
from typing import List, Dict, Tuple, Union, Any
from protocols.chat import ChatMessageRequest, ChatMessageResponse, ChatMessageVariantRequest, ContentType
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import time

from starlette.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN

import insights
from insights.api.query import TextQueryAPI
from insights.api.rate_limiter import rate_limit_middleware
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body, HTTPException
import uvicorn
from neurons import logger


class APIServer:

    failed_prompt_msg = "Please try again. Can't receive any responses from the miners or due to the poor network connection."

    def set_weights(self):
        """
        Sets the validator weights to the metagraph hotkeys based on the scores it has received from the miners. The weights determine the trust and incentive level the validator assigns to miner nodes on the network.
        """
        try:
            # Check if self.scores contains any NaN values and log a warning if it does.
            if np.isnan(self.scores).any():
                logger.warning(
                    f"Scores contain NaN values. This may be due to a lack of responses from miners, or a bug in your reward functions."
                )

            # Calculate the average reward for each uid across non-zero values.
            # Replace any NaN values with 0.
            raw_weights = np.linalg.norm(self.scores, p=1, dim=0)

            # Process the raw weights to final_weights via subtensor limitations.
            (
                processed_weight_uids,
                processed_weights,
            ) = bt.utils.weight_utils.process_weights_for_netuid(
                uids=self.metagraph.uids,
                weights=raw_weights,
                netuid=self.config.netuid,
                subtensor=self.subtensor,
                metagraph=self.metagraph,
            )

            # Convert to uint16 weights and uids.
            (
                uint_uids,
                uint_weights,
            ) = bt.utils.weight_utils.convert_weights_and_uids_for_emit(
                uids=processed_weight_uids, weights=processed_weights
            )
            table = Table(title="All Weights")
            table.add_column("uid", justify="right", style="cyan", no_wrap=True)
            table.add_column("weight", style="magenta")
            table.add_column("score", style="magenta")
            uids_and_weights = list(
                zip(uint_uids, uint_weights)
                )
            # Sort by weights descending.
            sorted_uids_and_weights = sorted(
                uids_and_weights, key=lambda x: x[1], reverse=True
            )
            for uid, weight in sorted_uids_and_weights:
                table.add_row(
                    str(uid),
                    str(round(weight, 4)),
                    str(int(self.scores[uid].item())),
                )
            console = Console()
            console.print(table)

            # Set the weights on chain via our subtensor connection.
            self.subtensor.set_weights(
                wallet=self.wallet,
                netuid=self.config.netuid,
                uids=processed_weight_uids,
                weights=processed_weights,
                wait_for_finalization=False,
                wait_for_inclusion=False,
                version_key=self.spec_version
            )

            with self.lock:
                self.last_weights_set_block = self.block

            logger.success("Finished setting weights.")
        except Exception as e:
            logger.error(
                f"Failed to set weights on chain with exception: { e }"
            )
    def is_response_status_code_valid(self, response):
            status_code = response.axon.status_code
            status_message = response.axon.status_message
            if response.is_failure:
                logger.info(f"Discovery response: Failure, miner {response.axon.hotkey} returned {status_code=}: {status_message=}")
            elif response.is_blacklist:
                logger.info(f"Discovery response: Blacklist, miner {response.axon.hotkey} returned {status_code=}: {status_message=}")
            elif response.is_timeout:
                logger.info(f"Discovery response: Timeout, miner {response.axon.hotkey}")
            return status_code == 200
        
    def get_reward(self, response: Union["bt.Synapse", Any], uid: int):
        return 0.5
        
    def update_scores(self, rewards: np.float32, uids: List[int]):
        """Performs exponential moving average on the scores based on the rewards received from the miners."""

        # Check if rewards contains NaN values.
        if np.isnan(rewards).any():
            logger.warning(f"NaN values detected in rewards: {rewards}")
            # Replace any NaN values in rewards with 0.
            rewards = np.nan_to_num(rewards, 0)

        # Check if `uids` is already a tensor and clone it to avoid the warning.
        if isinstance(uids, np.array):
            uids_tensor = uids.clone().detach()
        else:
            uids_tensor = np.array(uids)

        # Compute forward pass rewards, assumes uids are mutually exclusive.
        # shape: [ metagraph.n ]
        scattered_rewards: np.float32 = self.scores.scatter(
            0, uids_tensor, rewards
        )
        logger.debug(f"Scattered rewards: {rewards}")

        # Update scores with rewards produced by this step.
        # shape: [ metagraph.n ]
        alpha: float = self.config.user_query_moving_average_alpha
        self.scores: np.float32 = alpha * scattered_rewards + (
            1 - alpha
        ) * self.scores
        logger.debug(f"Updated moving avg scores: {self.scores}")
        
    def __init__(
            self,
            config: None,
            wallet: None,
            subtensor: None,
            metagraph: None,
        ):
        """
        API can be invoked while running a validator.
        Receive config, wallet, subtensor, metagraph from the validator and share the score of miners with the validator.
        subtensor and metagraph of APIs will change as the ones of validators change.
        """
        self.app = FastAPI(title="validator-api",
                           description="The goal of validator-api is to set up how to message between Chat API and validators.")

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.config = config
        self.device = self.config.neuron.device
        self.wallet = wallet
        self.text_query_api = TextQueryAPI(wallet=self.wallet)
        self.subtensor = subtensor
        self.metagraph = metagraph

        self.api_key_file_path = "api_key.json"
        self.api_keys = None
        self.rate_limit_config = {"requests": 1}
        if os.path.exists(self.api_key_file_path):
            with open(self.api_key_file_path, "r") as file:
                self.api_keys = json.load(file)

        self.config_file_path = "rate_limit.json"
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "r") as file:
                config = json.load(file)
                self.rate_limit_config = config.get("rate_limit", {"requests": 1})

        if self.api_keys:
            self.app.middleware("http")(self.rate_limit_middleware_factory(self.rate_limit_config["requests"]))

        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Request completed: {request.method} {request.url} in {duration:.4f} seconds")
            return response

        @self.app.post("/v1/api/text_query", summary="Processes chat message requests and returns a response from a randomly selected miner", tags=["v1"])
        async def get_response(request: Request, query: ChatMessageRequest = Body(..., example={
            "network": "bitcoin",
            "prompt": "Return 3 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
        })) -> ChatMessageResponse:
            if self.api_keys is not None:
                api_key_validator = self.get_api_key_validator()
                await api_key_validator(request)

            top_miner_uids = await get_top_miner_uids(metagraph=self.metagraph, wallet=wallet, top_rate=self.config.top_rate)
            logger.info(f"Top miner UIDs are {top_miner_uids}")

            selected_miner_uids = None
            if len(top_miner_uids) >= 3:
                selected_miner_uids = random.sample(top_miner_uids, 3)
            else:
                selected_miner_uids = top_miner_uids
            top_miner_axons = [metagraph.axons[uid] for uid in selected_miner_uids]

            logger.info(f"Top miner axons: {top_miner_axons}")

            if not top_miner_axons:
                raise HTTPException(status_code=503, detail=self.failed_prompt_msg)

            # get miner response
            responses, blacklist_axon_ids = await self.text_query_api(
                axons=top_miner_axons,
                network=query.network,
                text=query.prompt,
                timeout=self.config.timeout
            )

            if not responses:
                raise HTTPException(status_code=503, detail=self.failed_prompt_msg)

            blacklist_axons = np.array(top_miner_axons)[blacklist_axon_ids]
            blacklist_uids = np.where(np.isin(np.array(self.metagraph.axons), blacklist_axons))[0]
            responded_uids = np.setdiff1d(np.array(top_miner_uids), blacklist_uids)

            # Add score to miners respond to user query
            uids = responded_uids.tolist()
            rewards = [
                self.get_reward(response, uid) for response, uid in zip(responses, uids)
            ]
            # Remove None reward as they represent timeout cross validation
            filtered_data = [(reward, uid) for reward, uid in zip(rewards, uids) if reward is not None]

            if filtered_data:
                rewards, uids = zip(*filtered_data)

                rewards = np.float32(rewards)
                self.update_scores(rewards, uids)
            else:  
                logger.info('Skipping update_scores() as no responses were valid')

            # If the number of excluded_uids is bigger than top x percentage of the whole axons, format it.
            if len(self.excluded_uids) > int(self.metagraph.n * self.config.top_rate):
                logger.info(f"Excluded UID list is too long")
                self.excluded_uids = []            
            logger.info(f"Excluded_uids are {self.excluded_uids}")

            logger.info(f"Responses are {responses}")
            
            selected_index = responses.index(random.choice(responses))
            response_object = ChatMessageResponse(
                miner_hotkey=self.metagraph.axons[responded_uids[selected_index]].hotkey,
                response=responses[selected_index]
            )

            # return response and the hotkey of randomly selected miner
            return response_object

        @self.app.post("/v1/api/text_query/variant", summary="Processes variant chat message requests and returns a response from a specific miner", tags=["v1"])
        async def get_response_variant(request: Request, query: ChatMessageVariantRequest = Body(..., example={
            "network": "bitcoin",
            "prompt": "Return 3 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r",
            "miner_hotkey": "5EExDvawjGyszzxF8ygvNqkM1w5M4hA82ydBjhx4cY2ut2yr"
        })) -> ChatMessageResponse:
            if self.api_keys is not None:
                api_key_validator = self.get_api_key_validator()
                await api_key_validator(request)

            logger.info(f"Miner {query.miner_hotkey} received a variant request.")

            try:
                miner_id = metagraph.hotkeys.index(query.miner_hotkey)
            except ValueError:
                raise HTTPException(status_code=404, detail="Miner hotkey not found")

            miner_axon = [metagraph.axons[uid] for uid in [miner_id]]
            logger.info(f"Miner axon: {miner_axon}")

            responses, _ = await self.text_query_api(
                axons=miner_axon,
                network=query.network,
                text=query.prompt,
                timeout=self.config.timeout
            )

            if not responses:
                raise HTTPException(status_code=503, detail=self.failed_prompt_msg)

            # TODO: we store the responded UIDs to progres here and that data will be take later in scoring function
            # To be considered if that creates fair result, what i someone has a valdiator and will be prompting his own miner to get better score?
            # well, he wil pay for openai usage, so he will be paying for the score, so it is fair?

            logger.info(f"Variant: {responses}")
            response_object = ChatMessageResponse(
                miner_hotkey=query.miner_hotkey,
                response=responses[0]
            )

            return response_object

        @self.app.get("/", tags=["default"])
        def healthcheck():
            return {
                "status": "ok",
                "timestamp": datetime.utcnow()
            }

    def rate_limit_middleware_factory(self, max_requests):
        async def middleware(request: Request, call_next):
            return await rate_limit_middleware(request, call_next, max_requests)
        return middleware

    def get_api_key_validator(self):
        async def validator(request: Request):
            if self.api_keys is not None:
                api_key = request.headers.get("x-api-key")
                if not api_key or not any(api_key in keys for keys in self.api_keys):
                    return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"detail": "Forbidden"})
        return validator
        
    def start(self):
        # Set the default event loop policy to avoid conflicts with uvloop
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        # Start the Uvicorn server with your app
        uvicorn.run(self.app, host="0.0.0.0", port=int(self.config.api_port), loop="asyncio")
        
