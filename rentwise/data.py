"""Load the clean dataset with the right dtypes (see dataset/README.md)."""

from pathlib import Path

import pandas as pd

CLEAN_CSV = Path(__file__).resolve().parent.parent / "dataset" / "processed" / "apartments_clean.csv"


def load_listings(path: Path = CLEAN_CSV) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Build it with: uv run python scripts/clean_dataset.py"
        )
    return pd.read_csv(
        path,
        parse_dates=["listed_at"],
        dtype={"cats_allowed": "boolean", "dogs_allowed": "boolean"},
    )
