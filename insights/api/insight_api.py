import random
import asyncio
import numpy as np
from datetime import datetime
from protocols.chat import ChatMessageRequest, ChatMessageResponse, ChatMessageVariantRequest, ContentType
from fastapi.middleware.cors import CORSMiddleware
from insights.api.query import TextQueryAPI
from neurons.validators.utils.uids import get_top_miner_uids
from fastapi import FastAPI, Body, HTTPException
import uvicorn
from neurons import logger


class APIServer:

    failed_prompt_msg = "Please try again. Can't receive any responses from the miners or due to the poor network connection."

    def __init__(
            self,
            config: None,
            wallet: None,
            subtensor: None,
            metagraph: None
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
                "message_content": "Return 3 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r"
            }

            """

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
            # uids = responded_uids.tolist()
            # TODO: we store the responded UIDs to progres here and that data will be take later in scoring function
            # !! Score should go to miners hotkey not its uid !! uid can change but hotkey is unique

            selected_index = responses.index(random.choice(responses))
            response_object = ChatMessageResponse(
                miner_hotkey=self.metagraph.axons[responded_uids[selected_index]].hotkey,
                response=responses[selected_index]
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
                miner_id: int
            **Returns:**
            `ChatMessageResponse`: response in natural language.
                - `miner_id` (int): responded miner uid
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
                "message_content": "Return 3 transactions outgoing from my address bc1q4s8yps9my6hun2tpd5ke5xmvgdnxcm2qspnp9r",
                "temperature": "0.1",
                "miner_id": 230,
            }
            """
            logger.info(f"Miner {query.miner_hotkey} received a variant request.")

            miner = metagraph.hotkeys[query.miner_hotkey]
            miner_id = 24 # TODO !!
            miner_axon = metagraph.axons[miner_id]
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
        
    def start(self):
        # Set the default event loop policy to avoid conflicts with uvloop
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        # Start the Uvicorn server with your app
        uvicorn.run(self.app, host="0.0.0.0", port=int(self.config.api_port), loop="asyncio")
        
