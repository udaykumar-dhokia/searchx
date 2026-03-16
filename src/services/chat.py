from .search import search
from uuid import uuid1
from .process_url import process_url, ProcessUrlResult
from ..utils.retrieve import retrieve
from ..utils.rerank import rerank_chunks
from ..utils.generate_response import generate_response
import asyncio
from ..utils.insert_response import insert_response
from ..utils.insert_chat import insert_chat, update_chat_title
from typing import AsyncGenerator
from ..utils.event import event
import json
from uuid import UUID

async def chat(query: str, chat_id: UUID = None, response_id: UUID = None) -> AsyncGenerator[str, None]:

    if chat_id is None:
        chat_id = await insert_chat()

    if response_id is None:
        response_id = uuid1()

    yield event("status", message="Searching the web...")
    urls = await search(query)
    yield event("urls", urls=urls)

    yield event("status", message="Reading websites...")
    await asyncio.gather(
        *(process_url(url, response_id) for url in urls)
    )

    yield event("status", message="Retrieving relevant context...")
    relevant_chunks = await retrieve(query=query, response_id=response_id)
    reranked_chunks = await rerank_chunks(query=query, chunks=relevant_chunks)

    context = "\n\n".join([f"{r}" for r in reranked_chunks])

    yield event("status", message="Generating response...")
    title = ""
    content = ""

    async for chunk in generate_response(context=context, query=query):
        chunk_str = str(chunk).strip()
        if chunk_str.startswith("data:"):
            try:
                parts = chunk_str.split("data: ")
                for part in parts:
                    if not part.strip():
                        continue
                    data = json.loads(part.strip())
                    if data["type"] == "title":
                        title = data.get("text", "")
                    elif data["type"] == "content":
                        content += data.get("text", "")
            except Exception:
                pass

        yield chunk

    await update_chat_title(chat_id=chat_id, title=title)
    await insert_response(response_id=response_id, query=query, content=content, chat_id=chat_id, urls=urls)