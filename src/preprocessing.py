"""Cleaning pipeline for the UCI 'Apartment for Rent Classified' dataset (id 555).

Usage (from the repo root):
    uv run --with pandas python src/preprocessing.py

Reads  data/raw/apartments_for_rent_classified_100K.csv (unchanged original)
Writes data/processed/apartments_clean.csv and prints a step-by-step row log.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/apartments_for_rent_classified_100K.csv"
OUT = ROOT / "data/processed/apartments_clean.csv"

# Scope thresholds (documented in notebooks/PREPROCESSING_STEPS.md).
MIN_PRICE, MAX_PRICE = 300, 10_000          # USD per month
MIN_SQFT, MAX_SQFT = 150, 5_000             # square feet
MIN_PPSF, MAX_PPSF = 0.25, 10.0             # USD per sq ft per month
US_CENTROID = (39.8163, -98.5576)           # placeholder coordinates for unknown locations


def load_raw(path: Path = RAW) -> pd.DataFrame:
    # The file is ';'-separated and cp1252-encoded (UTF-8 decoding fails).
    return pd.read_csv(path, sep=";", encoding="cp1252", low_memory=False)


def clean(df: pd.DataFrame, verbose: bool = True) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    log: list[tuple[str, int]] = [("raw", len(df))]

    def step(name: str, frame: pd.DataFrame) -> pd.DataFrame:
        log.append((name, len(frame)))
        if verbose:
            print(f"{name:<55} {log[-2][1] - len(frame):>6} removed -> {len(frame):>6}")
        return frame

    df = step("1 drop exact duplicate rows", df.drop_duplicates())

    unit = ["body", "price", "square_feet", "bedrooms", "bathrooms", "latitude", "longitude"]
    df = df.sort_values("time").drop_duplicates(subset=unit, keep="last")
    df = step("2 drop reposts (same description + attributes, keep latest)", df)

    df = step("3 keep category housing/rent/apartment",
              df[df["category"] == "housing/rent/apartment"])
    df = step("4 keep monthly prices only", df[df["price_type"] == "Monthly"])

    df = step("5 drop missing price/bedrooms/bathrooms",
              df.dropna(subset=["price", "bedrooms", "bathrooms"]))

    placeholder = (df["latitude"] == US_CENTROID[0]) & (df["longitude"] == US_CENTROID[1])
    df = step("6 drop missing or placeholder location",
              df[~placeholder].dropna(subset=["cityname", "state", "latitude", "longitude"]))

    ppsf = df["price"] / df["square_feet"]
    in_scope = (df["price"].between(MIN_PRICE, MAX_PRICE)
                & df["square_feet"].between(MIN_SQFT, MAX_SQFT)
                & ppsf.between(MIN_PPSF, MAX_PPSF))
    df = step("7 drop implausible / out-of-scope price, size, price per sqft", df[in_scope])

    df = df.copy()
    # Feature preparation (no rows removed).
    amen = df["amenities"].fillna("").str.get_dummies(sep=",")
    amen = amen.loc[:, amen.columns != ""]  # newer pandas emits a column for empty strings
    amen.columns = ["amenity_" + c.lower().replace(" ", "_").replace("/", "_") for c in amen.columns]
    pets = df["pets_allowed"].fillna("")
    out = pd.DataFrame({
        "id": df["id"],
        "price": df["price"],
        "square_feet": df["square_feet"],
        "price_per_sqft": (df["price"] / df["square_feet"]).round(3),
        "bedrooms": df["bedrooms"].astype(int),
        "bathrooms": df["bathrooms"],
        "cityname": df["cityname"].str.strip(),
        "state": df["state"].str.strip(),
        "latitude": df["latitude"],
        "longitude": df["longitude"],
        "has_photo": df["has_photo"].ne("No").astype(int),
        "pets_cats": pets.str.contains("Cats").astype(int),
        "pets_dogs": pets.str.contains("Dogs").astype(int),
        "pets_unknown": df["pets_allowed"].isna().astype(int),
        "amenities_unknown": df["amenities"].isna().astype(int),
        "n_amenities": amen.sum(axis=1),
        "listed_at": pd.to_datetime(df["time"], unit="s"),
        "source": df["source"],
    }, index=df.index)
    out = pd.concat([out, amen], axis=1).sort_values("id").reset_index(drop=True)
    return out, log


if __name__ == "__main__":
    clean_df, _ = clean(load_raw())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUT, index=False)
    print(f"saved {clean_df.shape} -> {OUT.relative_to(ROOT)}")
