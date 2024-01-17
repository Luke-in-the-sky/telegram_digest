import pandas as pd
import pickle
from . import DATA_ASSETS_FOLDER, SWEEP_RESULTS_FILE
import logging
from .eval_utils import logging_setup
from .pydantic_models import XGBoostExplainer, LinearGAMExplainer
import json


def main():
    # load the results form the eval run
    with open(SWEEP_RESULTS_FILE, "r") as file:
        metrics_data = [json.loads(line) for line in file]

    # Filter only to stuff with multiple clusters
    df = pd.DataFrame(metrics_data).query("num_clusters > 1")
    nulls_to_zero_cols = [
        "num_samples_in_minus_1_cluster",
        "pct_samples_in_minus_1_cluster",
    ]
    df[nulls_to_zero_cols] = df[nulls_to_zero_cols].fillna(0)
    logging.debug(f"Filtered the Eval runs: {len(metrics_data)=}, {len(df)=}")

    # Example usage of fit_gam
    independent_vars = [
        # "hdbscan_alpha",
        # "hdbscan_cluster_selection_epsilon",
        # "hdbscan_min_cluster_size",
        "hdbscan_min_samples",
        "umap_min_dist",
        "umap_n_components",
        # "umap_n_neighbors",
        # "render_msg_upstream",
        "include_sender_name",
        "join_messages_n",
        # "join_messages_overlap",
        "num_of_samples",
    ]
    dependent_var = "silhouette_coefficient"

    lgam_expl = (
        LinearGAMExplainer(
            df=df, independent_vars=independent_vars, dependent_var=dependent_var
        )
        .train_model()
        .explain_and_plot(filepath=DATA_ASSETS_FOLDER / "LinearGAM_Expl.html")
    )

    xgboost_expl = (
        XGBoostExplainer(
            df=df, independent_vars=independent_vars, dependent_var=dependent_var
        )
        .train_model()
        .explain_and_plot(filepath=DATA_ASSETS_FOLDER / "XGBoost_Expl.png")
    )


if __name__ == "__main__":
    logging_setup()
    main()
