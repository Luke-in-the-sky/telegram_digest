import unittest
from clustering_metrics import compute_clustering_metrics
import numpy as np


class TestClusteringMetrics(unittest.TestCase):
    def test_compute_clustering_metrics(self):
        sample_to_vector = {1: [1.0, 2.0], 2: [2.0, 3.0], 3: [3.0, 4.0], 4: [5.0, 6.0]}
        sample_to_cluster = {1: 0, 2: 0, 3: 1, 4: 1}
        distance_metric = "euclidean"

        expected = {
            "Silhouette Coefficient": 0.33630952380952384,
            "Davies-Bouldin Index": 0.6000000000000001,
            "Calinski-Harabasz Index": 5.0,
            "Within-Cluster Sum of Squares": np.array([16.97056275, 19.79898987]),
        }

        metrics = compute_clustering_metrics(
            sample_to_vector, sample_to_cluster, distance_metric
        )

        self.assertDictEqual(expected, metrics)

    def test_empty_input(self):
        sample_to_vector = {}
        sample_to_cluster = {}
        distance_metric = "euclidean"

        metrics = compute_clustering_metrics(
            sample_to_vector, sample_to_cluster, distance_metric
        )

        self.assertEqual(metrics, {})


if __name__ == "__main__":
    unittest.main()
