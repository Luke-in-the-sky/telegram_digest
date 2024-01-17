from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.preprocessing import LabelEncoder
import numpy as np
from typing import Dict
from functools import lru_cache
import hashlib


def array_hash(X):
    return hashlib.sha256(
        X.tobytes() + str(X.shape).encode() + str(X.dtype).encode()
    ).hexdigest()


# Custom cache decorator for NumPy arrays
def numpy_array_cache(cache_func):
    cache = {}

    def wrapper(*args, **kwargs):
        hashable_args = tuple(
            [
                args[i] if not isinstance(args[i], np.ndarray) else array_hash(args[i])
                for i in range(len(args))
            ]
        )
        if hashable_args in cache:
            return cache[hashable_args]
        result = cache_func(*args, **kwargs)
        cache[hashable_args] = result
        return result

    return wrapper


@numpy_array_cache
def get_distance_matrix(X: np.array, metric: str) -> np.array:
    return pairwise_distances(X, metric=metric)


def compute_clustering_metrics(
    X: np.array, labels: np.array, distance_metric: str, exclude_neg_labels: bool = True
) -> Dict[str, float]:
    if exclude_neg_labels:
        mask = labels >= 0
        labels = labels[mask]
        X = X[mask]

    if len(set(labels)) < 2:
        return {}

    distance_matrix = get_distance_matrix(X, distance_metric)

    # Compute metrics using the provided distance matrix
    silhouette_avg = silhouette_score(distance_matrix, labels, metric="precomputed")

    return {
        "silhouette_coefficient": silhouette_avg,
        # if centroids are meaningful, we could also use
        #   davies_bouldin = davies_bouldin_score(X, labels_encoded)
        #   calinski_harabasz = calinski_harabasz_score(X, labels_encoded)
    }
