from uuid import UUID

from pydantic import BaseModel
from typing import List, Union, Optional
from enum import Enum

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

class ContentType(str, Enum):
    text = "text"
    graph = "graph"
    table = "table"

class TextContent(BaseModel):
    type: ContentType = ContentType.text
    content: str

class GraphNodeContent(BaseModel):
    id: str
    type: str
    label: str
    content: dict

class GraphEdgeContent(BaseModel):
    type: str
    from_id: str
    to_id: str
    content: dict

class GraphContent(BaseModel):
    type: ContentType = ContentType.graph
    content: List[Union[GraphNodeContent, GraphEdgeContent]]

class TableColumn(BaseModel):
    name: str
    label: str

class TableRow(BaseModel):
    id: str
    tx_id: str
    amount: int
    timestamp: int


class TableContent(BaseModel):
    type: ContentType = ContentType.table
    columns: List[TableColumn]
    content: List[TableRow]

class ChatMessageResponse(BaseModel):
    miner_id: str = ""
    response: List[Union[TextContent, GraphContent, TableContent]]