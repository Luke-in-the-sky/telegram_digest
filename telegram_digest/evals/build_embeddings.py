from embedding_manager import EmbeddingManager
from sentence_transformers import SentenceTransformer


def embed_docs(docs: List[str]):
    # build embeddings
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    emb_manager = EmbeddingManager(filename="./data_assets/emb_storage.pkl")
    return emb_manager.get_embeddings(sentence_model=sentence_model, docs=docs)