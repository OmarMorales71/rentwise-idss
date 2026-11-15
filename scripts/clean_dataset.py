"""Clean the UCI "Apartment for Rent Classified" dataset and compare raw vs clean.

Usage (from the repository root):

    python scripts/clean_dataset.py

Reads   dataset/raw/apartments_for_rent_classified_100K.csv  (never modified)
Writes  dataset/processed/apartments_clean.csv
        dataset/processed/cleaning_report.md   (raw vs clean comparison)

If the raw CSV is missing, the script downloads the UCI zip and extracts it
(extraction of the inner .7z needs `bsdtar` or `7z` on the PATH).

Every cleaning decision is explained in dataset/README.md.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "dataset" / "raw"
OUT_DIR = ROOT / "dataset" / "processed"
RAW_NAME = "apartments_for_rent_classified_100K"
UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/555/apartment+for+rent+classified.zip"

# --- Cleaning thresholds (see dataset/README.md for the rationale) -----------
PRICE_MIN, PRICE_MAX = 300, 10_000  # USD per month
SQFT_MIN, SQFT_MAX = 150, 5_000  # square feet
PPSF_MIN, PPSF_MAX = 0.30, 10.0  # USD per square foot per month
# Bounding box that contains the 50 US states (incl. Alaska and Hawaii).
LAT_MIN, LAT_MAX = 18.0, 72.0
LON_MIN, LON_MAX = -180.0, -65.0
# Geographic centre of the contiguous US: the source uses it as a placeholder
# when the real location of a listing is unknown.
PLACEHOLDER_COORDS = (39.8163, -98.5576)

# Listings that agree on all of these are treated as reposts of the same ad.
REPOST_KEY = [
    "price", "square_feet", "bedrooms", "bathrooms",
    "cityname", "state", "latitude", "longitude", "amenities", "source",
]
# Raw columns that are not carried over to the clean file.
DROPPED_COLUMNS = {
    "category": "constant after filtering out short-term rentals",
    "body": "long free text, not used by the models",
    "amenities": "replaced by amenities_listed and one amenity_* column per amenity",
    "currency": "constant (always USD)",
    "pets_allowed": "replaced by cats_allowed and dogs_allowed",
    "price_display": "formatted duplicate of price",
    "price_type": "constant after keeping monthly prices only",
    "address": "missing in 92% of the rows",
    "time": "replaced by listed_at (UTC timestamp)",
}
NUMERIC_COLUMNS = ["bathrooms", "bedrooms", "price", "square_feet", "latitude", "longitude"]


# --- Loading -----------------------------------------------------------------
def ensure_raw_csv(path: Path) -> None:
    """Download and extract the UCI archive if the raw CSV is not there yet."""
    if path.exists():
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / "apartment.zip"
    if not zip_path.exists():
        print(f"Downloading {UCI_ZIP_URL}")
        urllib.request.urlretrieve(UCI_ZIP_URL, zip_path)
    inner = f"{RAW_NAME}.7z"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extract(inner, RAW_DIR)
    tool = shutil.which("bsdtar") or shutil.which("7z") or shutil.which("7zz")
    if tool is None:
        raise SystemExit(f"Install 7-Zip (or bsdtar) and extract {RAW_DIR / inner} manually.")
    cmd = [tool, "-xf", inner] if tool.endswith("bsdtar") else [tool, "x", "-y", inner]
    subprocess.run(cmd, cwd=RAW_DIR, check=True)
    (RAW_DIR / inner).unlink()


def load_raw(path: Path) -> pd.DataFrame:
    """Read the raw file as text.

    The file is ';'-separated and cp1252-encoded. Titles and bodies contain
    stray '"' characters, so quoting must be disabled or rows get merged.
    Everything is read as text; types are converted explicitly afterwards.
    """
    return pd.read_csv(
        path, sep=";", dtype=str, encoding="cp1252",
        quoting=csv.QUOTE_NONE, keep_default_na=False,
    )


def normalise_missing(raw: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and turn the literal 'null' and empty strings into NA."""
    df = raw.apply(lambda col: col.str.strip())
    return df.mask(df.apply(lambda col: col.str.lower().isin(["null", ""])))


# --- Cleaning ----------------------------------------------------------------
def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def amenity_dummies(amenities: pd.Series) -> pd.DataFrame:
    """One 0/1 column per amenity; rows with no amenity list are all zeros."""
    dummies = amenities.fillna("").str.get_dummies(sep=",")
    dummies = dummies.loc[:, [c for c in dummies.columns if slug(c)]]
    dummies.columns = [f"amenity_{slug(c)}" for c in dummies.columns]
    return dummies


def clean(raw: pd.DataFrame, keep_reposts: bool = False) -> tuple[pd.DataFrame, list[dict]]:
    """Return the clean table and a log with the rows removed by each step."""
    log: list[dict] = []
    df = normalise_missing(raw)

    def keep(mask: pd.Series, step: str) -> None:
        nonlocal df
        before = len(df)
        df = df[mask.fillna(False)]
        log.append({"step": step, "removed": before - len(df), "remaining": len(df)})

    log.append({"step": "Raw file", "removed": 0, "remaining": len(df)})

    # 1. Exact duplicates (the same row, same id, appears twice).
    keep(~df.duplicated(), "Exact duplicate rows")

    # 2. Type conversion. Anything that is not a number becomes NA.
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Out-of-scope listings.
    keep(df["category"] != "housing/rent/short_term", "Short-term rentals")
    keep(df["price_type"] == "Monthly", "Price not quoted per month")
    keep(df["currency"] == "USD", "Currency other than USD")

    # 4. Rows without the fields the system cannot work without.
    keep(df["price"].notna() & df["square_feet"].notna(), "Missing price or square feet")
    placeholder = (df["latitude"] == PLACEHOLDER_COORDS[0]) & (df["longitude"] == PLACEHOLDER_COORDS[1])
    has_location = df[["cityname", "state", "latitude", "longitude"]].notna().all(axis=1)
    keep(has_location & ~placeholder, "Missing or placeholder location")

    # 5. Impossible values.
    valid = (
        (df["price"] > 0) & (df["square_feet"] > 0)
        & ~(df["bedrooms"] < 0) & ~(df["bathrooms"] <= 0)
        & df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LON_MIN, LON_MAX)
        & (df["state"].str.len() == 2)
    )
    keep(valid, "Impossible values (non-positive numbers, coordinates outside the US)")

    # 6. Implausible values (data-entry errors and out-of-scope luxury estates).
    keep(df["price"].between(PRICE_MIN, PRICE_MAX), f"Price outside ${PRICE_MIN:,}-${PRICE_MAX:,}")
    keep(df["square_feet"].between(SQFT_MIN, SQFT_MAX), f"Square feet outside {SQFT_MIN:,}-{SQFT_MAX:,}")
    ppsf = df["price"] / df["square_feet"]
    keep(ppsf.between(PPSF_MIN, PPSF_MAX), f"Price per sq ft outside ${PPSF_MIN:.2f}-${PPSF_MAX:.2f}")

    # 7. Reposts: the same unit advertised several times under different titles.
    if not keep_reposts:
        df = df.sort_values("time", kind="stable")  # keep the earliest ad
        keep(~df.duplicated(REPOST_KEY), "Reposts of the same listing")

    # 8. Impute the few missing bedroom / bathroom counts and flag them.
    df["bedrooms_imputed"] = df["bedrooms"].isna()
    size_band = pd.qcut(df["square_feet"], 10, duplicates="drop")
    df["bedrooms"] = df["bedrooms"].fillna(df.groupby(size_band, observed=True)["bedrooms"].transform("median"))
    df["bathrooms_imputed"] = df["bathrooms"].isna()
    df["bathrooms"] = df["bathrooms"].fillna(df.groupby("bedrooms")["bathrooms"].transform("median"))
    df["bathrooms"] = df["bathrooms"].fillna(df["bathrooms"].median())
    df["bedrooms"] = df["bedrooms"].round().astype(int)

    # 9. Derived columns.
    df["price"] = df["price"].astype(int)
    df["square_feet"] = df["square_feet"].astype(int)
    df["price_per_sqft"] = (df["price"] / df["square_feet"]).round(3)
    df["listed_at"] = pd.to_datetime(pd.to_numeric(df["time"]), unit="s", utc=True)
    df["fee"] = df["fee"] == "Yes"

    # Pets: missing = unknown (NA); "None" = no pets; contradictory = unknown.
    pets = df["pets_allowed"].str.split(",").apply(lambda v: set(v) if isinstance(v, list) else None)
    known = pets.notna() & ~pets.apply(lambda s: s is not None and "None" in s and len(s) > 1)
    for animal in ("Cats", "Dogs"):
        col = pets.apply(lambda s, a=animal: s is not None and a in s).astype("boolean")
        df[f"{animal.lower()}_allowed"] = col.where(known)

    # Amenities: one 0/1 column each. Missing list = no amenity recorded (all 0).
    df["amenities_listed"] = df["amenities"].notna()
    dummies = amenity_dummies(df["amenities"])
    df = pd.concat([df, dummies], axis=1)

    columns = [
        "id", "title", "price", "square_feet", "price_per_sqft",
        "bedrooms", "bathrooms", "bedrooms_imputed", "bathrooms_imputed",
        "cityname", "state", "latitude", "longitude",
        "cats_allowed", "dogs_allowed", "amenities_listed", *sorted(dummies.columns),
        "has_photo", "fee", "source", "listed_at",
    ]
    return df[columns].sort_values("id").reset_index(drop=True), log


# --- Raw vs clean comparison -------------------------------------------------
def md_table(headers: list[str], rows: list[list]) -> str:
    def fmt(v) -> str:
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else f"{v:,.2f}"
        if isinstance(v, (int, np.integer)):
            return f"{v:,}"
        return str(v)

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def pct(part: int, total: int) -> str:
    return f"{100 * part / total:.2f}%" if total else "n/a"


def build_report(raw: pd.DataFrame, clean_df: pd.DataFrame, log: list[dict], raw_path: Path) -> str:
    raw_na = normalise_missing(raw)
    n_raw, n_clean = len(raw), len(clean_df)
    out = [
        "# Cleaning report: raw vs clean",
        "",
        "Generated by `scripts/clean_dataset.py`. Do not edit by hand.",
        "",
        f"- Raw file: `{raw_path.relative_to(ROOT)}` ({n_raw:,} rows, {raw.shape[1]} columns)",
        f"- Clean file: `dataset/processed/apartments_clean.csv` ({n_clean:,} rows, {clean_df.shape[1]} columns)",
        f"- Rows kept: {pct(n_clean, n_raw)}",
        "",
        "## Rows removed by each step",
        "",
        md_table(
            ["Step", "Rows removed", "% of raw", "Rows remaining"],
            [[s["step"], s["removed"], pct(s["removed"], n_raw), s["remaining"]] for s in log],
        ),
        "",
        "## Raw columns: missing values and what happened to them",
        "",
        "Missing = empty or the literal text `null`. Invalid = present but not a number.",
        "",
    ]
    rows = []
    for col in raw.columns:
        missing = int(raw_na[col].isna().sum())
        invalid = int(pd.to_numeric(raw_na[col], errors="coerce").isna().sum()) - missing if col in NUMERIC_COLUMNS else 0
        if col in DROPPED_COLUMNS:
            status = f"dropped: {DROPPED_COLUMNS[col]}"
        else:
            status = f"kept, {int(clean_df[col].isna().sum()):,} missing"
        rows.append([f"`{col}`", missing, pct(missing, n_raw), invalid, status])
    out += [md_table(["Column", "Missing in raw", "% of raw", "Invalid in raw", "In clean file"], rows), ""]

    out += ["## New columns in the clean file", ""]
    new_rows = []
    for col in clean_df.columns:
        if col in raw.columns or col.startswith("amenity_"):
            continue
        s = clean_df[col]
        if s.dtype.name in ("bool", "boolean"):
            detail = f"true in {pct(int(s.sum()), n_clean)} of rows"
        elif col == "listed_at":
            detail = f"{s.min():%Y-%m-%d} to {s.max():%Y-%m-%d}"
        else:
            detail = f"median {s.median():,.2f}"
        new_rows.append([f"`{col}`", int(s.isna().sum()), detail])
    out += [md_table(["Column", "Missing", "Summary"], new_rows), ""]

    out += ["## Numeric columns: raw vs clean", ""]
    stat_rows = []
    for col in NUMERIC_COLUMNS:
        for label, s in (("raw", pd.to_numeric(raw_na[col], errors="coerce")), ("clean", clean_df[col].astype(float))):
            q = s.quantile([0.01, 0.5, 0.99])
            stat_rows.append([f"`{col}`", label, int(s.count()), s.min(), q[0.01], q[0.5], s.mean(), q[0.99], s.max()])
    out += [md_table(["Column", "Data", "Count", "Min", "P1", "Median", "Mean", "P99", "Max"], stat_rows), ""]

    out += ["## Listings per state (top 10 in raw)", ""]
    raw_states = raw_na["state"].value_counts()
    clean_states = clean_df["state"].value_counts()
    out += [md_table(
        ["State", "Raw rows", "Clean rows", "% kept"],
        [[st, int(n), int(clean_states.get(st, 0)), pct(int(clean_states.get(st, 0)), int(n))]
         for st, n in raw_states.head(10).items()],
    ), ""]

    out += ["## Amenities: share of listings (raw vs clean)", ""]
    raw_amen = amenity_dummies(raw_na["amenities"])
    out += [md_table(
        ["Column", "Raw", "Clean"],
        [[f"`{c}`", pct(int(raw_amen[c].sum()), n_raw), pct(int(clean_df[c].sum()), n_clean)]
         for c in sorted(raw_amen.columns)],
    ), ""]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--raw", type=Path, default=RAW_DIR / f"{RAW_NAME}.csv", help="raw CSV to clean")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="folder for the clean file and the report")
    parser.add_argument("--keep-reposts", action="store_true", help="do not remove reposted listings")
    args = parser.parse_args()

    ensure_raw_csv(args.raw)
    raw = load_raw(args.raw)
    clean_df, log = clean(raw, keep_reposts=args.keep_reposts)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(args.out_dir / "apartments_clean.csv", index=False)
    report = build_report(raw, clean_df, log, args.raw.resolve())
    (args.out_dir / "cleaning_report.md").write_text(report + "\n", encoding="utf-8")

    for s in log:
        print(f"{s['step']:<70} -{s['removed']:>6,}  -> {s['remaining']:>7,}")
    print(f"\nClean data: {args.out_dir / 'apartments_clean.csv'}")
    print(f"Comparison: {args.out_dir / 'cleaning_report.md'}")


if __name__ == "__main__":
    main()
