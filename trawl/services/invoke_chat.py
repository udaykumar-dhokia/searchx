from .chat import chat
from sqlalchemy import UUID
from dataclasses import dataclass
from ..utils.spawn_agent import spawn_agent
from typing import AsyncGenerator
from ..utils.event import event
from ..prompts.general import GENERAL_SEARCH_PROMPT
from ..prompts.social import SOCIAL_SEARCH_PROMPT

@dataclass
class AIResponse:
    """Response from AI"""
    enhanced_query: str
    image_query: str
    video_query: str

async def invoke_chat(query: str, chat_id: UUID = None, response_id: UUID = None, type: str = "general") -> AsyncGenerator[str, None]:

    yield event("status", message="Enhancing your query...")
    agent = spawn_agent(GENERAL_SEARCH_PROMPT if type == "general" else SOCIAL_SEARCH_PROMPT, AIResponse)

    try:
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
        )
    except AttributeError:
        import asyncio
        response = await asyncio.to_thread(
            agent.invoke,
            {"messages": [{"role": "user", "content": query}]}
        )

    enhanced_query = response["structured_response"].enhanced_query
    image_query = response["structured_response"].image_query
    video_query = response["structured_response"].video_query

    print(enhanced_query)

    async for chunk in chat(enhanced_query, image_query, video_query, chat_id, response_id):
        yield chunk