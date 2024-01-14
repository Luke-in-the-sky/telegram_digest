import UMAP
import hdbscan
from clustering_metrics import compute_clustering_metrics
import wandb


def cluster_and_eval(embeddings, umap_params: dict, hdbscan_params: dict):
    # reduce dimensionality
    reduced_emb = umap_model = UMAP(**umap_params).fit_transform(embeddings)

    # HDBSCAN
    clusterer = hdbscan.HDBSCAN(**hdbscan_params).fit(reduced_emb)
    # access with `clusterer.labels_``

    # Compute metrics
    metrics = compute_clustering_metrics(
        vectors=reduced_emb, labels=clusterer.labels_, distance_metric="cosine"
    )



def sweep_run():
    # Initialize a new W&B run each time this function is called
    with wandb.init() as run:
        # Retrieve hyperparameters
        config = wandb.config

        # Load embeddings
        embeddings = ...

        # Log the results
        wandb.log(cluster_and_eval(embeddings, **params))


# Sweep configuration
sweep_config = {
    'method': 'bayes',  # Bayesian optimization
    'metric': {
        'name': 'silhouette_coefficient',  # Metric to optimize
        'goal': 'maximize'  # or 'minimize' based on your key metric
    },
    'parameters': {
        'param1': {
            'values': [1, 2, 3]  # Example: range of values for a parameter
        },
        'param2': {
            'values': [0.1, 0.2, 0.3]  # Another parameter's range
        },
        # Add other parameters here
    }
}