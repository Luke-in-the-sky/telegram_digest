from typing import Generator, List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from umap import UMAP
import hdbscan
from .clustering_metrics import compute_clustering_metrics
import wandb
from . import DATA_ASSETS_FOLDER, DATASET_WITH_EMBEDDINGS_FILE
from .eval_utils import logging_setup
import logging

sweep_config_bayes = {
    "method": "bayes",  # Bayesian optimization
    "metric": {
        "name": "silhouette_coefficient",  # replace with your primary metric
        "goal": "maximize",  # or 'minimize' depending on your metric
    },
    "parameters": {
        "umap_n_neighbors": {"min": 5, "max": 50},
        "umap_min_dist": {"min": 0.0, "max": 1.0},
        "umap_n_components": {"min": 2, "max": 8},
        "hdbscan_min_cluster_size": {"min": 5, "max": 30},
        "hdbscan_min_samples": {"min": 1, "max": 30},
        "hdbscan_cluster_selection_epsilon": {"min": 0.0, "max": 0.5},
        "hdbscan_alpha": {"min": 0.5, "max": 1.5},
        # Add other parameters here
    },
}

sweep_config_grid = {
    "method": "grid",  # Grid search
    "metric": {
        "name": "silhouette_coefficient",  # replace with your primary metric
        "goal": "maximize",  # or 'minimize' depending on your metric
    },
    "parameters": {
        "umap_n_neighbors": {"values": [5, 50]},  # Only two values for grid search
        "umap_min_dist": {"values": [0.0, 1.0]},  # Only two values for grid search
        "hdbscan_min_cluster_size": {
            "values": [5, 50]
        },  # Only two values for grid search
        # Add other parameters with two values each
    },
}


def load_embeddings(
    path_to_file, group_by_cols: List[str]
) -> Generator[Tuple[Dict, np.array], None, None]:
    """
    1. loads the dataframe at path_to_file; this might represent more than 1 dataset.
    2. groups the df by the given columns
    3. yields 2 things:
        - a dict of the groupby columns and the corresponding values
        - the embeddings for each group
    """
    df = pd.read_pickle(path_to_file)
    logging.info(f"loaded dataframe with datasets: {len(df)=}")

    # compile dataset of all the embeddings for each grouping
    for setup_values, embs in (
        df.groupby(group_by_cols)
        .apply(lambda x: np.array(x.embedding.to_list()))
        .items()
    ):
        setup = dict(zip(group_by_cols, setup_values))
        logging.debug(f"{embs.shape=}; setup: {setup}")
        yield setup, embs


def compute_cluster_distribution(labels) -> Optional[Dict[str, float]]:
    """
    Compute the distribution of cluster sizes from a list of cluster labels.
    Exclude the noise label (-1) from the calculation.

    Parameters:
    labels (list or array): Cluster labels.

    Returns:
    dict: Dictionary with min, 5th percentile, median, average, 95th percentile.
    """
    # Filter out the noise (label = -1)
    filtered_labels = labels[labels != -1]

    # Check if the filtered array is empty
    if filtered_labels.size == 0:
        logging.debug("No valid clusters found (all labels are -1 or input is empty).")
        return None

    # Count the number of samples in each cluster
    unique, counts = np.unique(filtered_labels, return_counts=True)

    # Calculate the required statistics
    distribution = {
        "min": np.min(counts),
        "5th_perc": np.percentile(counts, 5),
        "median": np.median(counts),
        "average": np.mean(counts),
        "95th_perc": np.percentile(counts, 95),
    }

    return {f"cluster_distribution_{k}": v for k, v in distribution.items()}


def cluster_and_eval(
    embeddings: np.array, umap_params: dict, hdbscan_params: dict
) -> dict:
    reduced_emb = UMAP(**umap_params).fit_transform(embeddings)
    logging.debug(f"Reducing dimensions: {reduced_emb.shape=}")

    clusterer = hdbscan.HDBSCAN(**hdbscan_params).fit(reduced_emb)
    num_clusters = len(np.unique(clusterer.labels_))
    num_samples_in_minus_1_cluster = (
        np.sum(clusterer.labels_ == -1) if -1 in clusterer.labels_ else None
    )
    pct_samples_in_minus_1_cluster = (
        num_samples_in_minus_1_cluster * 1.0 / embeddings.shape[0]
        if num_samples_in_minus_1_cluster
        else None
    )
    logging.debug(f"Clustering: {clusterer.labels_.shape=}")

    metrics = compute_clustering_metrics(
        X=reduced_emb,
        labels=clusterer.labels_,
        distance_metric="cosine",
        exclude_neg_labels=True,
    )
    metrics.update(
        {
            "num_clusters": num_clusters,
            "num_samples_in_minus_1_cluster": num_samples_in_minus_1_cluster,
            "pct_samples_in_minus_1_cluster": pct_samples_in_minus_1_cluster,
            "num_of_samples": len(embeddings),
        }
    )
    if num_clusters > 1:
        metrics.update(**compute_cluster_distribution(clusterer.labels_))

    logging.debug(f"{metrics=}")

    return metrics


def sweep_run():
    with wandb.init() as run:
        # Retrieve hyperparameters
        config = wandb.config
        umap_params = {
            k.replace("umap_", ""): v
            for k, v in config.items()
            if k.startswith("umap_")
        }
        hdbscan_params = {
            k.replace("hdbscan_", ""): v
            for k, v in config.items()
            if k.startswith("hdbscan_")
        }

        # Load embeddings
        # list the complete set of columns that identifies a dataset
        # TODO: this should be exposed further out
        group_by_cols = [
            "render_msg_upstream",
            "include_sender_name",
            "join_messages_n",
            "join_messages_overlap",
        ]

        for dataset_setup, embeddings in load_embeddings(
            DATASET_WITH_EMBEDDINGS_FILE, group_by_cols
        ):
            metrics = cluster_and_eval(
                embeddings, umap_params=umap_params, hdbscan_params=hdbscan_params
            )

            clustering_params = {
                k: v
                for k, v in config.items()
                if k.startswith("umap_") or k.startswith("hdbscan_")
            }

            output = {**dataset_setup, **metrics, **clustering_params}
            logging.info(f"Output from Run: {output}")
            wandb.log(output)


if __name__ == "__main__":
    logging_setup()
    logging.info("Starting clustering sweep")

    with wandb.init(project="telegram_digest__test_clustering"):
        sweep_id = wandb.sweep(sweep_config_bayes)
        wandb.agent(sweep_id, sweep_run)


# def dummy_test():
#     group_by_cols = [
#         "render_msg_upstream",
#         "include_sender_name",
#         "join_messages_n",
#         "join_messages_overlap",
#     ]
#     loader = load_embeddings(DATASET_WITH_EMBEDDINGS_FILE, group_by_cols)
#     dataset_setup, embeddings = next(loader)
#     metrics = cluster_and_eval(
#         embeddings,
#         umap_params=dict(n_neighbors=5, min_dist=0.1),
#         hdbscan_params=dict(min_cluster_size=5),
#     )

#     print(dataset_setup)
#     print(metrics)
