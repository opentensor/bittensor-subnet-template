from uuid import UUID

from pydantic import BaseModel
from typing import List
from insights.protocol import QueryOutput


class ChatMessageRequest(BaseModel):
    network: str
    user_id: UUID
    prompt: str


class ChatMessageVariantRequest(BaseModel):
    network: str
    user_id: UUID
    prompt: str
    temperature: float
    miner_id: str


class ChatMessageResponse(BaseModel):
    miner_id: str = ""
    response: List[QueryOutput]