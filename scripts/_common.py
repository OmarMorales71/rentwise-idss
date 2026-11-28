"""Shared pieces of the validation scripts: data periods, metrics and Markdown tables.

Periods (report, Sections 4.5 and 5.2.3), all by posting date:

- fitting set:       before VALIDATION_FROM            (models for selection and calibration)
- validation period: VALIDATION_FROM .. before TEST_FROM (every choice is made here)
- training set:      before TEST_FROM                   (final models evaluated on test)
- test set:          from TEST_FROM                     (evaluated once, no choice made)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rentwise.data import load_listings  # noqa: E402

RESULTS = ROOT / "results"
VALIDATION_FROM = "2019-09-01"
TEST_FROM = "2019-12-01"


def _before(df: pd.DataFrame, day: str) -> pd.Series:
    return df["listed_at"] < pd.Timestamp(day, tz="UTC")


def load_periods() -> dict[str, pd.DataFrame]:
    """fit, validation, train and test sets, with a `city` key (city, state)."""
    df = load_listings()
    df = df.assign(city=df["cityname"] + ", " + df["state"])
    train = df[_before(df, TEST_FROM)].reset_index(drop=True)
    test = df[~_before(df, TEST_FROM)].reset_index(drop=True)
    fit = train[_before(train, VALIDATION_FROM)].reset_index(drop=True)
    validation = train[~_before(train, VALIDATION_FROM)].reset_index(drop=True)
    return {"fit": fit, "validation": validation, "train": train, "test": test}


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    ape = np.abs(pred - y) / y
    return {"MAE (USD)": np.mean(np.abs(pred - y)), "MAPE": ape.mean(), "MdAPE": np.median(ape),
            "Within ±10%": (ape <= .10).mean(), "Within ±25%": (ape <= .25).mean()}


def fmt(column: str, value) -> str:
    if isinstance(value, str):
        return value
    if "USD" in column:
        return f"{value:,.0f}"
    if column.startswith("n ") or column in ("Listings", "Count"):
        return f"{value:,.0f}"
    if "distance" in column.lower() or column in ("Value",):
        return f"{value:.2f}"
    return f"{value:.1%}"


def md_table(rows: dict[str, dict] | list[tuple[str, dict]], first: str = "Model") -> str:
    rows = list(rows.items()) if isinstance(rows, dict) else rows
    cols = list(rows[0][1])
    lines = ["| " + " | ".join([first, *cols]) + " |",
             "|" + "|".join("---" for _ in range(len(cols) + 1)) + "|"]
    for name, row in rows:
        lines.append("| " + " | ".join([name, *(fmt(c, v) for c, v in row.items())]) + " |")
    return "\n".join(lines)


def write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWritten to {path}")
