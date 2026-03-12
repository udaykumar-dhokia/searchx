import faiss
from src.core.config import INDEX_PATH

def build_faiss_index(embeddings, save_path=INDEX_PATH):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    
    faiss.write_index(index, save_path)
    print(f"Index saved to {save_path}")
    return index