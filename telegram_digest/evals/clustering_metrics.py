from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.preprocessing import LabelEncoder
import numpy as np
from typing import Dict, List


def compute_clustering_metrics(
    vectors: List, labels: List, distance_metric: str
) -> Dict[str, float]:
    # Convert vectors and labels to numpy arrays
    X = np.array(vectors)
    labels = np.array(labels)

    # Encode labels to integers
    le = LabelEncoder()
    labels_encoded = le.fit_transform(labels)

    # Calculate pairwise distance matrix
    distance_matrix = pairwise_distances(X, metric=distance_metric)

    # Compute metrics
    silhouette_avg = silhouette_score(
        distance_matrix, labels_encoded, metric="precomputed"
    )
    davies_bouldin = davies_bouldin_score(X, labels_encoded)
    calinski_harabasz = calinski_harabasz_score(X, labels_encoded)

    # Compute Within-Cluster Sum of Squares
    unique_labels = np.unique(labels_encoded)
    wcss = sum(
        np.sum(distance_matrix[labels_encoded == label, :], axis=1)
        for label in unique_labels
    )

    return {
        "silhouette_coefficient": silhouette_avg,
        "davies-bouldin_index": davies_bouldin,
        "calinski-Harabasz_index": calinski_harabasz,
        "within-cluster_sum_of_squares": wcss,
    }


# # Example usage
# sample_to_vector = {
#     1: [1.0, 2.0],
#     2: [2.0, 3.0],
#     3: [3.0, 4.0],
#     4: [5.0, 6.0]
# }
# sample_to_cluster = {
#     1: 0,
#     2: 0,
#     3: 1,
#     4: 1
# }
# distance_metric = 'euclidean'

# metrics = compute_clustering_metrics(sample_to_vector, sample_to_cluster, distance_metric)
# print(metrics)
