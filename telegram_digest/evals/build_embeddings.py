import pandas as pd
from embedding_manager import EmbeddingManager
from build_docs import DOCS_OUTPUT_FOLDER
from sentence_transformers import SentenceTransformer
from typing import List


def embed_docs(docs: List[str]):
    model_name = "all-MiniLM-L6-v2"
    # build embeddings
    sentence_model = SentenceTransformer(model_name)
    emb_manager = EmbeddingManager(filename="./data_assets/emb_storage.pkl")
    return emb_manager.get_embeddings(embedding_model=sentence_model, model_name=model_name, docs=docs)

def testing():
    df = pd.read_pickle(DOCS_OUTPUT_FOLDER/'docs_testing.pkl')
    return embed_docs(df.doc[:2].tolist())



if __name__ == "__main__":
    testing()
