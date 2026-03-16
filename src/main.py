from fastapi import FastAPI
from pydantic import BaseModel
from .db.database import engine
from .models import Base
from fastapi    .responses import StreamingResponse
from .models.response import Response
from .models.documents import Document, DocumentChunk
from .models.chat import Chat
from .services.invoke_chat import invoke_chat
from typing import Optional
from uuid import UUID

app = FastAPI()

Base.metadata.create_all(bind=engine)

class ChatRequest(BaseModel):
    query: str
    chat_id: Optional[UUID] = None
    response_id: Optional[UUID] = None

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/chat")
async def chat(body: ChatRequest):
    return StreamingResponse(
        invoke_chat(query=body.query, chat_id=body.chat_id,response_id=body.response_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )