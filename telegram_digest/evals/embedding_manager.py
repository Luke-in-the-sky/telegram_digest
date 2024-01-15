import pickle
from typing import Iterable, List, Union
from eval_utils import hash_this


class EmbeddingManager:
    def __init__(self, filename: Union[str, List[str]] = None):
        self.data = {}
        self.filename = filename

        if filename:
            self.load_from_file(filename)

    def load_from_file(self, filename: Union[str, List[str]] = None):
        if isinstance(filename, str):
            filenames = [filename]
        for name in filenames:
            with open(name, "rb") as file:
                self.data.update(pickle.load(file))

    def write_to_file(self, filename=None):
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    def get_embeddings(self, embedding_model, docs: Union[str, Iterable[str]]) -> List:
        """
        Returns a list of embeddings for the given docs.
        If possible, pulls pre-computed embeddings from the local data
        """
        try:
            model_name = embedding_model.model_name
        except AttributeError:
            raise AttributeError("Model name attribute not found in embedding_model")

        if isinstance(docs, str):
            docs = [docs]

        # Generate a unique identifier
        hashes_to_index = {
            hash_this([model_name, doc]): i for doc, i in enumerate(docs)
        }

        # Check which documents already have embeddings in storage
        embeddings_map = {
            hash: self.data.get(hash) for hash in hashes_to_index if hash in self.data
        }

        # embed new docs
        hashes_of_new_docs = list(hashes_to_index.keys() - embeddings_map.keys())
        new_docs = [docs[hashes_to_index[hash]] for hash in hashes_of_new_docs]
        new_embeddings = embedding_model.encode(
            new_docs
        )  # process the list `new_docs` , so we can take advantage of batching

        # Combine the new embedding with the existing embeddings
        self.data.update(
            {
                hash: embedding
                for hash, embedding in zip(hashes_of_new_docs, new_embeddings)
            }
        )

        # return embeddings in the original order of the docs
        return [
            self.data[hash]
            for hash in sorted(hashes_to_index.keys(), key=lambda x: hashes_to_index[x])
        ]
