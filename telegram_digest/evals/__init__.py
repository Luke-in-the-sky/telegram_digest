from pathlib import Path
DATA_ASSETS_FOLDER = Path("./data_assets/")

folder = DATA_ASSETS_FOLDER
if not folder.exists():
    folder.mkdir()