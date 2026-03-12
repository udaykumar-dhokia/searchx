from src.utils.fetch_page import fetch_page
from src.utils.extract_text import extract_text
from src.utils.chunk_text import chunk_text

def process_url(url):
    """Process a single URL: fetch -> extract -> chunk"""
    html = fetch_page(url)
    text = extract_text(html)
    if text:
        chunks = list(chunk_text(text))
        return url, chunks
    return url, []