import pandas as pd
from embedding_manager import EmbeddingManager
from build_docs import DOCS_OUTPUT_FOLDER
from sentence_transformers import SentenceTransformer


def embed_docs(docs: List[str]):
    # build embeddings
    sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    emb_manager = EmbeddingManager(filename="./data_assets/emb_storage.pkl")
    return emb_manager.get_embeddings(sentence_model=sentence_model, docs=docs)

def testing():
    df = pd.read_pickle(DOCS_OUTPUT_FOLDER/'docs_testing.pkl')

    return embed_docs(df.doc[:3].tolist())



if __name__ == "__main__":
    asyncio.run(testing())
