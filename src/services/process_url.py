from ..utils.fetch_page import fetch_page
from ..utils.extract_text import extract_text
from ..utils.chunk_text import chunk_text
from ..utils.insert_document import insert_document
from ..utils.batch_insert_embeddings import batch_insert_embeddings
from sqlalchemy import UUID
from .embeddings import create_embeddings
from typing import List
from dataclasses import dataclass

@dataclass
class ProcessUrlResult:
    document_id: UUID | None
    document_chunk_ids: List[UUID]

async def process_url(url: str, response_id: UUID) -> ProcessUrlResult:
    """Process a url and return a ProcessUrlResult"""

    html = fetch_page(url)
    text: str | None = extract_text(html)

    if text:
        document_id = await insert_document(content=text, response_id=response_id)
        chunks = list(chunk_text(text))

        embeddings = await create_embeddings(chunks)
        document_chunk_ids = await batch_insert_embeddings(chunk_texts=chunks, embeddings=embeddings, document_id=document_id, response_id=response_id)

        return ProcessUrlResult(
            document_id=document_id,
            document_chunk_ids=document_chunk_ids or []
        )

    return ProcessUrlResult(
        document_id=None,
        document_chunk_ids=[]
    )