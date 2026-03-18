from .search import search
from uuid import uuid1
from .process_url import process_url
from ..utils.retrieve import retrieve
from ..utils.rerank import rerank_chunks
from ..utils.spawn_agent import spawn_agent
from ..prompts.deepsearch import DEEPSEARCH_VERTICALS_PROMPT, DEEPSEARCH_RESPONSE_PROMPT
from ..core.config import get_llm
import asyncio
from ..utils.insert_response import insert_response
from ..utils.insert_chat import insert_chat, update_chat_title
from typing import AsyncGenerator, List
from ..utils.event import event
import json
from uuid import UUID
from dataclasses import dataclass
import httpx
from ..core.config import SEARXNG_BASE_URL


@dataclass
class DeepSearchVerticals:
    """Response containing 3 search verticals."""
    vertical_1: str
    vertical_2: str
    vertical_3: str


async def search_vertical(query: str, num_results: int = 15) -> List[str]:
    """Search for a single vertical and return URLs."""
    if not SEARXNG_BASE_URL:
        return []

    params = {
        "q": query,
        "format": "json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{SEARXNG_BASE_URL}/search",
                params=params,
                timeout=30
            )
            data = response.json()
            return [r["url"] for r in data.get("results", [])[:num_results]]
    except Exception:
        return []


async def deepsearch_chat(query: str, image_query: str, video_query: str, chat_id: UUID = None, response_id: UUID = None) -> AsyncGenerator[str, None]:
    """DeepSearch pipeline: 3 verticals × 15 URLs = 45 sources → detailed response."""

    if chat_id is None:
        chat_id = await insert_chat()

    if response_id is None:
        response_id = uuid1()

    yield event("status", message="DeepSearch: Analyzing query into research verticals...")

    agent = spawn_agent(DEEPSEARCH_VERTICALS_PROMPT, DeepSearchVerticals)

    try:
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
        )
    except AttributeError:
        response = await asyncio.to_thread(
            agent.invoke,
            {"messages": [{"role": "user", "content": query}]}
        )

    verticals_response = response["structured_response"]
    verticals = [
        verticals_response.vertical_1,
        verticals_response.vertical_2,
        verticals_response.vertical_3,
    ]

    yield event("deepsearch_verticals", verticals=verticals)

    all_urls = []
    vertical_urls_map = {}

    for i, vertical in enumerate(verticals):
        yield event("vertical_progress", vertical_index=i, vertical_query=vertical, status="searching")

        urls = await search_vertical(vertical, num_results=15)
        vertical_urls_map[vertical] = urls
        all_urls.extend(urls)

        yield event("vertical_progress", vertical_index=i, vertical_query=vertical, status="done", url_count=len(urls))

    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    yield event("deepsearch_urls", urls=unique_urls, vertical_urls=vertical_urls_map, total=len(unique_urls))
    yield event("urls", urls=unique_urls)

    image_urls = []
    video_urls = []
    if SEARXNG_BASE_URL:
        try:
            async with httpx.AsyncClient() as client:
                image_search_params = {"q": image_query, "categories": "images", "format": "json"}
                video_search_params = {"q": video_query, "categories": "videos", "format": "json"}
                
                img_res, vid_res = await asyncio.gather(
                    client.get(url=f"{SEARXNG_BASE_URL}/search", params=image_search_params, timeout=15),
                    client.get(url=f"{SEARXNG_BASE_URL}/search", params=video_search_params, timeout=15),
                    return_exceptions=True
                )
                
                if isinstance(img_res, httpx.Response) and img_res.status_code == 200:
                    image_urls = [r.get("img_src", "") for r in img_res.json().get("results", [])[:5] if r.get("img_src")]
                
                if isinstance(vid_res, httpx.Response) and vid_res.status_code == 200:
                    video_urls = [r.get("url", "") for r in vid_res.json().get("results", [])[:5] if r.get("url")]
        except Exception:
            pass
            
    yield event("image_urls", image_urls=image_urls)
    yield event("video_urls", video_urls=video_urls)

    yield event("status", message=f"DeepSearch: Reading {len(unique_urls)} sources...")

    batch_size = 10
    for i in range(0, len(unique_urls), batch_size):
        batch = unique_urls[i:i + batch_size]
        yield event("status", message=f"DeepSearch: Reading sources {i+1}-{min(i+batch_size, len(unique_urls))} of {len(unique_urls)}...")
        await asyncio.gather(
            *(process_url(url, response_id) for url in batch)
        )

    yield event("status", message="DeepSearch: Analyzing and ranking information...")
    relevant_chunks = await retrieve(query=query, response_id=response_id)
    reranked_chunks = await rerank_chunks(query=query, chunks=relevant_chunks)

    context = "\n\n".join([f"{r}" for r in reranked_chunks])

    yield event("status", message="DeepSearch: Generating comprehensive response...")

    prompt = DEEPSEARCH_RESPONSE_PROMPT.format(context=context, query=query)

    title = ""
    content = ""

    yield event("status", message="DeepSearch: Writing detailed analysis...")

    async for chunk in get_llm().astream(prompt):
        if chunk.content:
            text = chunk.content
            content += text
            yield event("content", text=text)

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break

    if not title:
        title = f"Deep Research: {query[:40]}" + ("..." if len(query) > 40 else "")

    yield event("title", text=title)

    await update_chat_title(chat_id=chat_id, title=title)
    await insert_response(
        response_id=response_id,
        query=query,
        content=content,
        chat_id=chat_id,
        urls=unique_urls,
        image_urls=image_urls,
        video_urls=video_urls
    )

    yield event("done", chat_id=str(chat_id))
