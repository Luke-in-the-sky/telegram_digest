from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.preprocessing import LabelEncoder
import numpy as np
from typing import Dict
import hashlib

# Global cache for distance matrices
distance_matrix_cache = {}


def array_hash(X):
    return hashlib.sha256(X.data.tobytes()).hexdigest()


def compute_clustering_metrics(
    X: np.array, labels: np.array, distance_metric: str, exclude_neg_labels: bool = True
) -> Dict[str, float]:
    if exclude_neg_labels:
        mask = labels >= 0
        labels = labels[mask]
        vectors = vectors[mask]

    if len(set(labels)) < 2:
        return {}

    # Encode labels to integers
    le = LabelEncoder()
    labels_encoded = le.fit_transform(labels)

    # Calculate pairwise distance matrix
    X_hash = array_hash(X)
    try:
        distance_matrix = distance_matrix_cache[X_hash]
    except KeyError:
        distance_matrix = pairwise_distances(X, metric=distance_metric)
        distance_matrix_cache[X_hash] = distance_matrix

    # Compute metrics
    silhouette_avg = silhouette_score(
        distance_matrix, labels_encoded, metric="precomputed"
    )

    # if centroids are meaningful, we could also use
    # davies_bouldin = davies_bouldin_score(X, labels_encoded)
    # calinski_harabasz = calinski_harabasz_score(X, labels_encoded)

    return {
        "silhouette_coefficient": silhouette_avg,
    }
