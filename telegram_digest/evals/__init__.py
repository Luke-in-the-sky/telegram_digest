from pathlib import Path
DATA_ASSETS_FOLDER = Path("telegram_digest/evals/data_assets/")
DATASET_WITH_EMBEDDINGS_FILE = DATA_ASSETS_FOLDER / "dataset_with_embeddings.pkl"

folder = DATA_ASSETS_FOLDER
if not folder.exists():
    folder.mkdir()