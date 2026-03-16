from ..core.config import LLM
from typing import AsyncGenerator
from .event import event

async def generate_response(context: str, query: str) -> AsyncGenerator[str, None]:
    """Generate a response using streaming tokens for real-time feedback."""
    
    prompt = f"""
    You are an expert AI assistant. Strictly use the context below to answer the user's question clearly and concisely.
    Use Markdown for formatting. Include a relevant title at the very beginning of your response bolded like # Title.
    
    Context:
    {context}
    
    Question: {query}
    """

    yield event("status", message="Thinking...")
    
    first_token = True
    async for chunk in LLM.astream(prompt):
        if first_token:
            yield event("status", message="Generating response...")
            first_token = False
        
        # Stream the content directly
        if chunk.content:
            yield event("content", text=chunk.content)