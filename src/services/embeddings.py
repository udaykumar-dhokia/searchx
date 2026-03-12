from sentence_transformers import SentenceTransformer, CrossEncoder

def create_embeddings(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(chunks)