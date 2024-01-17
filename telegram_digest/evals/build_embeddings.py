import pandas as pd
from .embedding_manager import EmbeddingManager
from sentence_transformers import SentenceTransformer
from typing import List
import logging
from . import DATA_ASSETS_FOLDER, DATASET_WITH_EMBEDDINGS_FILE
from .eval_utils import logging_setup


def embed_docs(
    docs: List[str],
    model_name: str = "all-MiniLM-L6-v2",
    embedding_storage_file=DATA_ASSETS_FOLDER / "emb_storage.pkl",
) -> List:
    # build embeddings
    sentence_model = SentenceTransformer(model_name)
    emb_manager = EmbeddingManager(filename=embedding_storage_file)
    emb = emb_manager.get_embeddings(
        embedding_model=sentence_model, model_name=model_name, docs=docs
    )
    emb_manager.write_to_file(embedding_storage_file)

    return emb


if __name__ == "__main__":
    paths_to_docs_dataset = [
        # DATA_ASSETS_FOLDER / "docs_testing.pkl",
        # DATA_ASSETS_FOLDER / "docs_testing_2.pkl",
        # DATA_ASSETS_FOLDER / "docs_testing_3.pkl",
        # DATA_ASSETS_FOLDER / "docs_testing_4.pkl",
        DATA_ASSETS_FOLDER / "docs_testing_10.pkl",
        ]

    # Configure logging
    logging_setup()
    logging.info("Starting")
    logging.debug(f"loading from these paths: {paths_to_docs_dataset}")

    # run
    df = pd.concat([pd.read_pickle(fp) for fp in paths_to_docs_dataset])
    emb = embed_docs(
        df.doc.tolist(),
        model_name="all-MiniLM-L6-v2",
        embedding_storage_file=DATA_ASSETS_FOLDER / "emb_storage.pkl",
    )

    assert len(emb) == len(df), f"len(emb)={len(emb)}!= len(df)={len(df)}"
    df["embedding"] = emb
    logging.info(f"Saving to {DATASET_WITH_EMBEDDINGS_FILE}")
    df.to_pickle(DATASET_WITH_EMBEDDINGS_FILE)
    logging.info("Done")
