from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    network: str
    user_id: int
    prompt: str
    
class ChatMessageResponse(BaseModel):
    text: str
    miner_id: str