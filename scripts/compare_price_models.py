"""Compare candidate price models for the price assessment (A1).

Usage (from the repository root, after scripts/clean_dataset.py):

    python scripts/compare_price_models.py

Reads   dataset/processed/apartments_clean.csv
Writes  results/price_model_comparison.md

Temporal split: listings posted before December 2019 are the training data,
listings posted in December 2019 (the last collection period) are the test
data. Models compared: a naive city median, KNN comparables, Ridge regression
on log(price) with and without amenities, and a Random Forest on log(price).
The decision based on these results is explained in
report/price_model_decision.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset" / "processed" / "apartments_clean.csv"
OUT = ROOT / "results" / "price_model_comparison.md"

TEST_FROM = "2019-12-01"  # first day of the test period
NUM = ["square_feet", "bedrooms", "bathrooms"]
MIN_COMPARABLES = 10  # below this, KNN widens the search from the city to the state
KNN_KS = (5, 10, 20)
RIDGE_ALPHA = 1.0
RF_PARAMS = dict(n_estimators=200, min_samples_leaf=3, n_jobs=-1, random_state=0)


# --- Data --------------------------------------------------------------------
def load(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    df = pd.read_csv(path, parse_dates=["listed_at"])
    df["city"] = df["cityname"] + ", " + df["state"]
    is_test = df["listed_at"] >= pd.Timestamp(TEST_FROM, tz="UTC")
    amenities = [c for c in df.columns if c.startswith("amenity_")]
    return df[~is_test].reset_index(drop=True), df[is_test].reset_index(drop=True), amenities


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    ape = np.abs(pred - y) / y
    return {"MAE (USD)": np.mean(np.abs(pred - y)), "MAPE": ape.mean(), "MdAPE": np.median(ape),
            "Within ±10%": (ape <= .10).mean(), "Within ±25%": (ape <= .25).mean()}


# --- Models ------------------------------------------------------------------
def naive_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Median price in the same city with the same bedrooms; else the city; else the state."""
    by_city_bed = train.groupby(["city", "bedrooms"]).price.median()
    by_city = train.groupby("city").price.median()
    by_state = train.groupby("state").price.median()
    return np.array([by_city_bed.get((c, b), by_city.get(c, by_state.get(s)))
                     for c, b, s in zip(test.city, test.bedrooms, test.state)], dtype=float)


def knn_predict(train: pd.DataFrame, test: pd.DataFrame, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Median price of the k nearest listings in the city (or state, if the city is too small).

    Returns the predictions (NaN when no reference) and the evidence level of each
    test listing: 'city', 'state' or 'none'.
    """
    mu, sd = train[NUM].mean(), train[NUM].std()
    z_train = ((train[NUM] - mu) / sd).to_numpy()
    z_test = ((test[NUM] - mu) / sd).to_numpy()
    prices = train.price.to_numpy()
    by_city, by_state = train.groupby("city").indices, train.groupby("state").indices
    pred = np.full(len(test), np.nan)
    level = np.full(len(test), "none", dtype=object)
    for city, idx in test.groupby("city").indices.items():
        cand, lvl = by_city.get(city, np.array([], dtype=int)), "city"
        if len(cand) < MIN_COMPARABLES:
            cand, lvl = by_state.get(test.state.iloc[idx[0]], np.array([], dtype=int)), "state"
        if len(cand) < MIN_COMPARABLES:
            continue
        nn = NearestNeighbors(n_neighbors=min(k, len(cand))).fit(z_train[cand])
        _, neighbours = nn.kneighbors(z_test[idx])
        pred[idx] = np.median(prices[cand][neighbours], axis=1)
        level[idx] = lvl
    return pred, level


def ridge_predict(train: pd.DataFrame, test: pd.DataFrame, amenities: list[str]) -> np.ndarray:
    """Ridge on log(price): standardised log area, bedrooms, bathrooms; one-hot city and state."""
    def numeric(d: pd.DataFrame) -> pd.DataFrame:
        return d[NUM].assign(square_feet=np.log(d.square_feet))
    x_train, x_test = numeric(train), numeric(test)
    mu, sd = x_train.mean(), x_train.std()
    enc = OneHotEncoder(handle_unknown="ignore")
    c_train, c_test = enc.fit_transform(train[["city", "state"]]), enc.transform(test[["city", "state"]])
    X_train = sparse.hstack([((x_train - mu) / sd).to_numpy(), train[amenities].to_numpy(), c_train]).tocsr()
    X_test = sparse.hstack([((x_test - mu) / sd).to_numpy(), test[amenities].to_numpy(), c_test]).tocsr()
    model = Ridge(alpha=RIDGE_ALPHA).fit(X_train, np.log(train.price))
    return np.exp(model.predict(X_test))


def rf_predict(train: pd.DataFrame, test: pd.DataFrame, amenities: list[str]) -> np.ndarray:
    """Random Forest on log(price), with a city mean log price computed on the training data only."""
    states = {s: i for i, s in enumerate(sorted(set(train.state) | set(test.state)))}
    log_price = np.log(train.price)
    city_mean, state_mean = log_price.groupby(train.city).mean(), log_price.groupby(train.state).mean()

    def features(d: pd.DataFrame) -> pd.DataFrame:
        x = d[NUM + ["latitude", "longitude"] + amenities].copy()
        x["state"] = d.state.map(states)
        x["city_log_price"] = d.city.map(city_mean).fillna(d.state.map(state_mean))
        return x

    model = RandomForestRegressor(**RF_PARAMS).fit(features(train), log_price)
    return np.exp(model.predict(features(test)))


# --- Report ------------------------------------------------------------------
def md_table(rows: dict[str, dict] | list[tuple[str, dict]], first: str = "Model") -> str:
    rows = list(rows.items()) if isinstance(rows, dict) else rows
    cols = list(rows[0][1])
    lines = ["| " + " | ".join([first, *cols]) + " |", "|" + "|".join("---" for _ in range(len(cols) + 1)) + "|"]
    for name, row in rows:
        cells = [str(v) if isinstance(v, str) else (f"{v:,.0f}" if "USD" in c else f"{v:.1%}")
                 for c, v in row.items()]
        lines.append("| " + " | ".join([name, *cells]) + " |")
    return "\n".join(lines)


def gap_row(y: np.ndarray, pred: np.ndarray) -> dict:
    gap = (y - pred) / pred
    p50, p75, p90 = np.percentile(np.abs(gap), [50, 75, 90])
    return {"Median signed gap": float(np.median(gap)), "Absolute gap P50": p50, "P75": p75, "P90": p90}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    train, test, amenities = load(args.data)
    y = test.price.to_numpy()
    knn = {k: knn_predict(train, test, k) for k in KNN_KS}
    p_knn, level = knn[10]
    has_ref, city = ~np.isnan(p_knn), level == "city"
    p_ridge_amen = ridge_predict(train, test, amenities)
    p_ridge = ridge_predict(train, test, [])
    p_rf = rf_predict(train, test, amenities)

    all_models = {"Naive: city median, same bedrooms": metrics(y, naive_predict(train, test))}
    for k, (p, _) in knn.items():
        ok = ~np.isnan(p)
        all_models[f"KNN, k = {k}"] = metrics(y[ok], p[ok])
    all_models["Ridge, log(price), with amenities"] = metrics(y, p_ridge_amen)
    all_models["Ridge, log(price), without amenities"] = metrics(y, p_ridge)
    all_models["Random Forest, log(price)"] = metrics(y, p_rf)

    by_level = {}
    for lvl, label in (("city", "Same city"), ("state", "Same state (fallback)"), ("none", "None")):
        m = level == lvl
        row = {"Share of test listings": m.mean()}
        if lvl != "none":
            row.update({k: v for k, v in metrics(y[m], p_knn[m]).items() if k in ("MAE (USD)", "MAPE", "Within ±25%")})
        else:
            row.update({"MAE (USD)": "–", "MAPE": "–", "Within ±25%": "–"})
        by_level[label] = row

    models = {"KNN, k = 10": p_knn, "Ridge with amenities": p_ridge_amen,
              "Ridge without amenities": p_ridge, "Random Forest": p_rf}
    same_rows = [(name, {"Rows": label, **metrics(y[m], pred[m])})
                 for label, m in (("all with a KNN reference", has_ref), ("city level", city))
                 for name, pred in models.items()]
    gaps = {name: gap_row(y[city], pred[city]) for name, pred in models.items()}

    out = [
        "# Price model comparison (A1)",
        "",
        "Generated by `scripts/compare_price_models.py`. Do not edit by hand.",
        "The decision based on these results is explained in `report/price_model_decision.md`.",
        "",
        f"- Data: `{args.data.relative_to(ROOT) if args.data.is_relative_to(ROOT) else args.data}`",
        f"- Train: {len(train):,} listings posted before {TEST_FROM}",
        f"- Test: {len(test):,} listings posted from {TEST_FROM} (December 2019)",
        f"- Test listings in a city that appears in the training data: {test.city.isin(set(train.city)).mean():.1%}",
        f"- KNN: same city, widened to the state below {MIN_COMPARABLES} listings; standardised {', '.join(NUM)}",
        f"- Ridge: alpha = {RIDGE_ALPHA}; Random Forest: {RF_PARAMS['n_estimators']} trees, "
        f"min_samples_leaf = {RF_PARAMS['min_samples_leaf']}",
        "",
        "## All models",
        "",
        "KNN rows exclude the test listings for which no reference could be computed.",
        "",
        md_table(all_models),
        "",
        "## KNN (k = 10) by evidence level",
        "",
        md_table(by_level, first="Comparables found in"),
        "",
        "## Same test listings for every model",
        "",
        md_table(same_rows),
        "",
        "## Gap between asking rent and reference (city-level test listings)",
        "",
        "Gap = (asking rent - reference) / reference.",
        "",
        md_table(gaps),
        "",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
