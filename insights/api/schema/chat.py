from uuid import UUID

from pydantic import BaseModel

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
    text: str
    miner_id: str