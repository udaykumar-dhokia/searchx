import faiss
import os
from src.core.config import INDEX_PATH

def load_faiss_index(save_path=INDEX_PATH, dim=128):
    if os.path.exists(save_path):
        index = faiss.read_index(save_path)
        print(f"Index loaded from {save_path}")
    else:
        index = faiss.IndexFlatL2(dim)
        print(f"No existing index found. Created new index.")
    return index