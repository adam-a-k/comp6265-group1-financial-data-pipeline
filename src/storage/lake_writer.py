import json
from pathlib import Path
from datetime import datetime

def write_to_lake(dataset, record):

    folder = Path("data_lake") / dataset
    folder.mkdir(parents=True, exist_ok=True)

    file = folder / f"{datetime.utcnow().date()}.json"

    with open(file, "a") as f:
        f.write(json.dumps(record) + "\n")