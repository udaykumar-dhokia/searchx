import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")
SEARXNG_BASE_URL=os.getenv("SEARXNG_BASE_URL")
INDEX_PATH = "faiss_index.idx"
