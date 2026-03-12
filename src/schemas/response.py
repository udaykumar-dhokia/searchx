import uuid
from pydantic import BaseModel
from typing import List
import time

class Response(BaseModel):
    id: uuid.UUID
    vector_id: uuid.UUID
    query: str
    sources: List[str]
    response: str
    created_at: time
