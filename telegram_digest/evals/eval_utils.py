import logging
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

def logging_setup(filename: str='logfile.log'):
    logging.basicConfig(
        level=logging.INFO,
        # level=logging.DEBUG,
        # datefmt='%Y-%m-%d %H:%M:%S',
        datefmt="%H:%M:%S",
        format="%(asctime)s %(levelname)s |%(name)s| %(message)s",
        handlers=[logging.FileHandler(filename), logging.StreamHandler()],
    )

    