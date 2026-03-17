from fastapi import FastAPI
from pydantic import BaseModel
from ..db.database import engine, SessionLocal
from ..models import Base
from fastapi.responses import StreamingResponse
from ..models.response import Response
from ..models.chat import Chat
from ..services.invoke_chat import invoke_chat
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Depends
import uvicorn
import os

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    query: str
    chat_id: Optional[UUID] = None
    response_id: Optional[UUID] = None
    type: Optional[str] = "general"

@app.get("/")
def root():
    return {"message": "Server is running"}

@app.post("/chat")
async def chat(body: ChatRequest):
    return StreamingResponse(
        invoke_chat(query=body.query, chat_id=body.chat_id, response_id=body.response_id, type=body.type),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

@app.get("/chats")
def get_chats(db: Session = Depends(get_db)):
    return db.query(Chat).order_by(Chat.created_at.desc()).all()

@app.get("/responses")
def get_responses(chat_id: UUID, db: Session = Depends(get_db)):
    return db.query(Response).filter(Response.chat_id == chat_id).order_by(Response.created_at).all()

def run_api():
    """Entry point for the trawl-api command."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting trawl API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)