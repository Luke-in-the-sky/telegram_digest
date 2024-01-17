from pathlib import Path
DATA_ASSETS_FOLDER = Path("telegram_digest/evals/data_assets/")
DATASET_WITH_EMBEDDINGS_FILE = DATA_ASSETS_FOLDER / "dataset_with_embeddings.pkl"
SWEEP_RESULTS_FILE = DATA_ASSETS_FOLDER / "sweep_results.jsonl"

folder = DATA_ASSETS_FOLDER
if not folder.exists():
    folder.mkdir()


# run the following modules in order
    # build_docs
    # build_embeddings
    # eval_run
    # eval_review