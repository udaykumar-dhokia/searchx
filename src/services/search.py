import httpx
from dotenv import load_dotenv
from typing import List
from ..core.config import SEARXNG_BASE_URL

load_dotenv()

async def search(query: str) -> List[str]:
    """Search for the relevant websites asynchronously"""

    if not SEARXNG_BASE_URL:
        return []
    
    params = {
        "q": query,
        "format": "json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url=f"{SEARXNG_BASE_URL}/search", params=params)
        data = response.json()

    urls = [r["url"] for r in data["results"][:15]]

    return urls