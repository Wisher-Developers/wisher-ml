from sentence_transformers import SentenceTransformer

def create_single_embedding(description: str):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Generate the embedding
    embedding = model.encode(description)
    return embedding
