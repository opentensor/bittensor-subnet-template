import argparse
import os
import random
import time

import asyncio
import numpy as np
from typing import List, Optional, Union, Any, Dict
from datetime import datetime
import traceback
import torch
import bittensor as bt
from rich.table import Table
from rich.console import Console
import yaml

from fastapi.middleware.cors import CORSMiddleware
from insights import protocol
from insights.protocol import QueryOutput
from insights.api.query import TextQueryAPI
from insights.api.get_query_axons import get_query_api_axons
from insights.api.schema.chat import ChatMessageRequest, ChatMessageResponse, ChatMessageVariantRequest, TextContent, GraphContent, GraphNodeContent, ContentType, GraphEdgeContent, TableContent, TableRow, TableColumn
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body
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
            if torch.isnan(self.scores).any():
                logger.warning(
                    f"Scores contain NaN values. This may be due to a lack of responses from miners, or a bug in your reward functions."
                )

            # Calculate the average reward for each uid across non-zero values.
            # Replace any NaN values with 0.
            raw_weights = torch.nn.functional.normalize(self.scores, p=1, dim=0)

            # Process the raw weights to final_weights via subtensor limitations.
            (
                processed_weight_uids,
                processed_weights,
            ) = bt.utils.weight_utils.process_weights_for_netuid(
                uids=self.metagraph.uids.to("cpu"),
                weights=raw_weights.to("cpu"),
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
        
    def update_scores(self, rewards: torch.FloatTensor, uids: List[int]):
        """Performs exponential moving average on the scores based on the rewards received from the miners."""

        # Check if rewards contains NaN values.
        if torch.isnan(rewards).any():
            logger.warning(f"NaN values detected in rewards: {rewards}")
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
        logger.debug(f"Scattered rewards: {rewards}")

        # Update scores with rewards produced by this step.
        # shape: [ metagraph.n ]
        alpha: float = self.config.user_query_moving_average_alpha
        self.scores: torch.FloatTensor = alpha * scattered_rewards + (
            1 - alpha
        ) * self.scores.to(self.device)
        logger.debug(f"Updated moving avg scores: {self.scores}")
        
    def __init__(
            self,
            config: None,
            wallet: None,
            subtensor: None,
            metagraph: None,
            scores: None,
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
        self.excluded_uids = []
        self.scores = scores

        @self.app.post("/api/text_query", summary="POST /natural language query", tags=["validator api"])
        async def get_response(query: ChatMessageRequest = Body(...)):
            """
            Generate a response to user query

            This endpoint allows miners convert the natural language query from the user into a Cypher query, and then provide a concise response in natural language.
            
            **Parameters:**
            `query` (ChatMessageRequest): natural language query from users, network(Bitcoin, Ethereum, ...), User ID.
                network: str
                user_id: UUID
                prompt: str

            **Returns:**
            `ChatMessageResponse`: response in natural language.
                - `miner_id` (str): responded miner uid
                - `response` (json): miner response containing the following types of information:
                1. Text information in natural language
                2. Graph information for funds flow model-based response
                3. Tabular information for transaction and account balance model-based response
            
            **Example Request:**
            ```json
            POST /text-query
            {
                "network": "Bitcoin",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
                "message_content": "Show me 15 transactions I sent after block height 800000. My address is bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
            }
            ```

            **Example Response:**
            ```json
            {
                "miner_id": "5CUUjNeTr5WAB7q4VqBkGrCyJ9XRZ4wqQMRZBw2XTmrR3xQA",
                "response": [
                {
                    "type": "text",
                    "content": "Hello, this is the answer from you"
                },
                {
                    "type": "graph",
                    "content": [
                    {
                        "id": "bc9zc38fha93idi823rf0wa94fj",
                        "type": "node",
                        "label": "address",
                        "content": {
                            "address": "bc9zc38fha93idi823rf0wa94fj"
                        }
                    },
                    {
                        "id": "bc9zc38fha93idi823rf0wa943223",
                        "type": "node",
                        "label": "transaction",
                        "content": {
                            "address": "bc9zc38fha93idi823rf0wa943223"
                        }
                    },
                    {
                        "type": "edge",
                        "from_id": "bc9zc38fha93idi823rf0wa94fj",
                        "to_id": "bc9zc38fha93idi823rf0wa943223",
                        "content": {}
                    }
                    ]
                },
                {
                    "type": "table",
                    "columns": [
                    {
                        "name": "tx_id",
                        "label": "Transaction Id"
                    },
                    {
                        "name": "amount",
                        "label": "Amount"
                    },
                    {
                        "name": "timestamp",
                        "label": "Timestamp"
                    }
                    ],
                    "content": [
                    {
                        "id": "0x123",
                        "tx_id": "0x123",
                        "amount": 300,
                        "timestamp": 102932123123
                    },
                    {
                        "id": "0x456",
                        "tx_id": "0x456",
                        "amount": 450,
                        "timestamp": 103924927430
                    }
                    ]
                }
                ]
            }

            ```
            """
            # select top miner            
            top_miner_uids = get_top_miner_uids(self.metagraph, self.config.top_rate, self.excluded_uids)
            logger.info(f"Top miner UIDs are {top_miner_uids}")
            top_miner_axons = await get_query_api_axons(wallet=self.wallet, metagraph=self.metagraph, uids=top_miner_uids)
            logger.info(f"Top miner axons: {top_miner_axons}")

            # get miner response
            responses, blacklist_axon_ids = await self.text_query_api(
                axons=top_miner_axons,
                network=query.network,
                text=query.prompt,
                timeout=self.config.timeout
            )

            blacklist_axons = np.array(top_miner_axons)[blacklist_axon_ids]
            blacklist_uids = np.where(np.isin(np.array(self.metagraph.axons), blacklist_axons))[0]
            # get responded miner uids among top miners
            responded_uids = np.setdiff1d(np.array(top_miner_uids), blacklist_uids)
            self.excluded_uids = np.union1d(np.array(self.excluded_uids), blacklist_uids)
            self.excluded_uids = self.excluded_uids.astype(int).tolist()
            logger.info(f"Excluded_uids are {self.excluded_uids}")

            if not responses:
                return ChatMessageResponse(response=[TextContent(content=self.failed_prompt_msg)])

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
                logger.info('Skipping update_scores() as no responses were valid')

            # If the number of excluded_uids is bigger than top x percentage of the whole axons, format it.
            if len(self.excluded_uids) > int(self.metagraph.n * self.config.top_rate):
                logger.info(f"Excluded UID list is too long")
                self.excluded_uids = []            
            logger.info(f"Excluded_uids are {self.excluded_uids}")

            logger.info(f"Responses are {responses}")
            
            selected_index = responses.index(random.choice(responses))

            # Example records for graph and table representations
            graph_example = GraphContent(
                content=[
                    GraphNodeContent(
                        id="bc9zc38fha93idi823rf0wa94fj",
                        type="node",
                        label="address",
                        content={"address": "bc9zc38fha93idi823rf0wa94fj"}
                    ),
                    GraphNodeContent(
                        id="bc9zc38fha93idi823rf0wa943223",
                        type="node",
                        label="transaction",
                        content={"address": "bc9zc38fha93idi823rf0wa943223"}
                    ),
                    GraphEdgeContent(
                        type="edge",
                        from_id="bc9zc38fha93idi823rf0wa94fj",
                        to_id="bc9zc38fha93idi823rf0wa943223",
                        content={}
                    )
                ]
            )

            table_example = TableContent(
                columns=[
                    TableColumn(name="tx_id", label="Transaction Id"),
                    TableColumn(name="amount", label="Amount"),
                    TableColumn(name="timestamp", label="Timestamp")
                ],
                content=[
                    TableRow(id="0x123", tx_id="0x123", amount=300, timestamp=102932123123),
                    TableRow(id="0x456", tx_id="0x456", amount=450, timestamp=103924927430)
                ]
            )

            response_object = ChatMessageResponse(
                miner_id=self.metagraph.hotkeys[responded_uids[selected_index]],
                response=[
                    TextContent(content=responses[selected_index].interpreted_result),
                    graph_example,
                    table_example
                ]
            )

            # return response and the hotkey of randomly selected miner
            return response_object

        @self.app.post("/api/text_query/variant", summary="POST /variation request for natual language query", tags=["validator api"])
        async def get_response_variant(query: ChatMessageVariantRequest = Body(...)):
            """            
            A validator would be able to receive a user request to generate a variation on a previously generated message. It will return the new message and store the fact that a specific miner's message had a variation request.
            - Receive temperature. The temperature will determine the creativity of the response.
            - Return generated variation text and miner ID.

            
            **Parameters:**
            `query` (ChatMessageVariantRequest): natural language query from users, network(Bitcoin, Ethereum, ...), User ID, Miner UID, temperature.\
                user_id: UUID
                prompt: str
                temperature: float
                miner_id: str
            **Returns:**
            `ChatMessageResponse`: response in natural language.
                - `miner_id` (str): responded miner uid
                - `response` (json): miner response containing the following types of information:
                1. Text information in natural language
                2. Graph information for funds flow model-based response
                3. Tabular information for transaction and account balance model-based response
            
            **Example Request:**
            ```json
            POST /text-query
            {
                "network": "Bitcoin",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message_content": "Show me 15 transactions I sent after block height 800000. My address is bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r",
                "temperature": "0.1",
                miner_id: "230",
            }
            ```

            **Example Response:**
            ```json
            {
                "miner_id": "5CUUjNeTr5WAB7q4VqBkGrCyJ9XRZ4wqQMRZBw2XTmrR3xQA",
                "response": [
                {
                    "type": "text",
                    "content": "Hello, this is the answer from you"
                },
                {
                    "type": "graph",
                    "content": [
                    {
                        "id": "bc9zc38fha93idi823rf0wa94fj",
                        "type": "node",
                        "label": "address",
                        "content": {
                            "address": "bc9zc38fha93idi823rf0wa94fj"
                        }
                    },
                    {
                        "id": "bc9zc38fha93idi823rf0wa943223",
                        "type": "node",
                        "label": "transaction",
                        "content": {
                            "address": "bc9zc38fha93idi823rf0wa943223"
                        }
                    },
                    {
                        "type": "edge",
                        "from_id": "bc9zc38fha93idi823rf0wa94fj",
                        "to_id": "bc9zc38fha93idi823rf0wa943223",
                        "content": {}
                    }
                    ]
                },
                {
                    "type": "table",
                    "columns": [
                    {
                        "name": "tx_id",
                        "label": "Transaction Id"
                    },
                    {
                        "name": "amount",
                        "label": "Amount"
                    },
                    {
                        "name": "timestamp",
                        "label": "Timestamp"
                    }
                    ],
                    "content": [
                    {
                        "id": "0x123",
                        "tx_id": "0x123",
                        "amount": 300,
                        "timestamp": 102932123123
                    },
                    {
                        "id": "0x456",
                        "tx_id": "0x456",
                        "amount": 450,
                        "timestamp": 103924927430
                    }
                    ]
                }
                ]
            }

            ```
            """
            logger.info(f"Miner {query.miner_id} received a variant request.")
            
            miner_axon = await get_query_api_axons(wallet=self.wallet, metagraph=self.metagraph, uids=query.miner_id)
            logger.info(f"Miner axon: {miner_axon}")
            
            responses, _ = await self.text_query_api(
                axons=miner_axon,
                network=query.network,
                text=query.prompt,
                timeout=self.config.timeout
            )
            
            if not responses:
                return ChatMessageResponse(response=[TextContent(content=self.failed_prompt_msg)])
            
            logger.info(f"Variant: {responses}")

            # Example records for graph and table representations
            graph_example = GraphContent(
                content=[
                    GraphNodeContent(
                        id="bc9zc38fha93idi823rf0wa94fj",
                        type="node",
                        label="address",
                        content={"address": "bc9zc38fha93idi823rf0wa94fj"}
                    ),
                    GraphNodeContent(
                        id="bc9zc38fha93idi823rf0wa943223",
                        type="node",
                        label="transaction",
                        content={"address": "bc9zc38fha93idi823rf0wa943223"}
                    ),
                    GraphEdgeContent(
                        type="edge",
                        from_id="bc9zc38fha93idi823rf0wa94fj",
                        to_id="bc9zc38fha93idi823rf0wa943223",
                        content={}
                    )
                ]
            )

            table_example = TableContent(
                columns=[
                    TableColumn(name="tx_id", label="Transaction Id"),
                    TableColumn(name="amount", label="Amount"),
                    TableColumn(name="timestamp", label="Timestamp")
                ],
                content=[
                    TableRow(id="0x123", tx_id="0x123", amount=300, timestamp=102932123123),
                    TableRow(id="0x456", tx_id="0x456", amount=450, timestamp=103924927430)
                ]
            )

            response_object = ChatMessageResponse(
                miner_id=query.miner_id,
                response=[
                    TextContent(content=responses[0].interpreted_result),
                    graph_example,
                    table_example
                ]
            )

            return response_object

        @self.app.get("/", tags=["default"])
        def healthcheck():
            return datetime.utcnow()  
        
    def start(self):
        # Set the default event loop policy to avoid conflicts with uvloop
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        # Start the Uvicorn server with your app
        uvicorn.run(self.app, host="0.0.0.0", port=int(self.config.api_port), loop="asyncio")
        
