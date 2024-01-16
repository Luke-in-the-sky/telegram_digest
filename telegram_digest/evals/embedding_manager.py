import pickle
from typing import Iterable, List, Union
from eval_utils import hash_this
import logging
from pathlib import Path


class EmbeddingManager:
    def __init__(self, filename: Union[Path, List[Path]] = None):
        self.data = {}
        self.filename = filename
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing EmbeddingManager")

        if filename:
            self.load_from_file(filename)

    def load_from_file(self, filename: Union[Path, List[Path]] = None):
        if isinstance(filename, Path):
            filename = [filename]
        for name in filename:
            if name.exists():
                self.logger.info(f"Loading embeddings from {name}")
                with open(name, "rb") as file:
                    self.data.update(pickle.load(file))

    def write_to_file(self, filename=None):
        self.logger.info(f"Saving to {filename}")
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    def get_embeddings(
        self, embedding_model, model_name: str, docs: Union[str, Iterable[str]]
    ) -> List:
        """
        Returns a list of embeddings for the given docs.
        If possible, pulls pre-computed embeddings from the local data
        """
        if isinstance(docs, str):
            docs = [docs]
        self.logger.debug(f"docs to embedd: {len(docs)=}")
        hashes = [hash_this([model_name, doc]) for doc in docs]

        idx_to_embeddings = {}
        new_docs_indexes = []
        for i, hash in enumerate(hashes):
            if hash in self.data:
                idx_to_embeddings[i] = self.data[hash]
            else:
                new_docs_indexes.append(i)
        new_docs = [docs[i] for i in new_docs_indexes]
        self.logger.debug(
            f"Loaded known emb: {len(idx_to_embeddings)=}. new docs: {len(new_docs)=}"
        )

        # embed new docs
        # we want to pass them all at once to the encoder, so that
        # we can take advantage of batching (as opposed to mapping a call to
        # the encoder to each doc)
        new_embeddings = embedding_model.encode(new_docs)
        idx_to_embeddings.update(dict(zip(new_docs_indexes, new_embeddings)))
        self.logger.debug(f"loaded new idx-to-emb: {len(idx_to_embeddings)=}")

        # Combine the new embedding with the existing embeddings
        self.logger.info(f"Updating embedding storage")
        self.data.update(
            {hashes[idx]: embedding for idx, embedding in idx_to_embeddings.items()}
        )

        # return embeddings in the original order of the docs
        assert len(idx_to_embeddings) == len(
            docs
        ), f"We seem to be missing some embeddings, {len(idx_to_embeddings)=}, {len(docs)=}"
        return [idx_to_embeddings[i] for i in range(len(docs))]
