import hashlib
from typing import Iterable

def hash_this(hashable_pieces: Iterable) -> str:
    """
    Hash a list of hashable pieces of data.
    """
    hasher = hashlib.sha256()
    for piece in hashable_pieces:
        hasher.update(str(piece).encode())
    return hasher.hexdigest()