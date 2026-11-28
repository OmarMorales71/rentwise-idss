"""Compare candidate price models for the price assessment (A1).

Usage (from the repository root, after scripts/clean_dataset.py):

    uv run python scripts/compare_price_models.py

Reads   dataset/processed/apartments_clean.csv
Writes  results/price_model_comparison.md

Periods are defined in scripts/_common.py. The Ridge penalty alpha and the KNN
k are chosen on the validation period (models fitted on the fitting set); the
models are then refitted on the training set and compared once on the test
set. The test set is not used for any choice.

The system's models (Ridge reference and KNN comparables) come from the
rentwise package, so these results describe the code the application runs.
The naive baseline and the Random Forest exist only for comparison.
The decision based on these results is explained in report/price_model_decision.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from _common import RESULTS, TEST_FROM, VALIDATION_FROM, load_periods, md_table, metrics, write
from rentwise import config
from rentwise.price import KNN_ATTRIBUTES, RidgeKnnPriceAssessor, build_reference_model

OUT = RESULTS / "price_model_comparison.md"
KNN_KS = (5, 10, 20)
RIDGE_ALPHAS = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)
RF_PARAMS = dict(n_estimators=200, min_samples_leaf=3, n_jobs=-1, random_state=0)


# --- Models ------------------------------------------------------------------
def naive_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Median price in the same city with the same bedrooms; else the city; else the state."""
    by_city_bed = train.groupby(["city", "bedrooms"]).price.median()
    by_city = train.groupby("city").price.median()
    by_state = train.groupby("state").price.median()
    return np.array([by_city_bed.get((c, b), by_city.get(c, by_state.get(s)))
                     for c, b, s in zip(test.city, test.bedrooms, test.state)], dtype=float)


def knn_predict(train: pd.DataFrame, test: pd.DataFrame, k: int) -> tuple[np.ndarray, np.ndarray]:
    """KNN used as an estimator: median price of the system's k comparables.

    NaN when fewer than min(k, MIN_COMPARABLES) comparables exist. Also returns
    the evidence level of each test listing ('city', 'state' or 'none').
    """
    nb = RidgeKnnPriceAssessor(train, k=k).neighbours(test)
    prices = train.price.to_numpy(dtype=float)
    neighbour_prices = np.where(nb.index >= 0, prices[nb.index], np.nan)
    pred = np.nanmedian(np.where(nb.n[:, None] > 0, neighbour_prices, 0.0), axis=1)
    pred[nb.n < min(k, config.MIN_COMPARABLES)] = np.nan
    return pred, nb.level


def ridge_predict(train: pd.DataFrame, test: pd.DataFrame, alpha: float,
                  amenities: list[str] | None = None) -> np.ndarray:
    """The system's Ridge reference (optionally with amenity indicators)."""
    cols = KNN_ATTRIBUTES + ["city", "state"] + list(amenities or [])
    model = build_reference_model(alpha, tuple(amenities or ()))
    model.fit(train[cols], np.log(train.price))
    return np.exp(model.predict(test[cols]))


def rf_predict(train: pd.DataFrame, test: pd.DataFrame, amenities: list[str]) -> np.ndarray:
    """Random Forest on log(price), with a city mean log price computed on the training data only."""
    states = {s: i for i, s in enumerate(sorted(set(train.state) | set(test.state)))}
    log_price = np.log(train.price)
    city_mean, state_mean = log_price.groupby(train.city).mean(), log_price.groupby(train.state).mean()

    def features(d: pd.DataFrame) -> pd.DataFrame:
        x = d[KNN_ATTRIBUTES + ["latitude", "longitude"] + amenities].copy()
        x["state"] = d.state.map(states)
        x["city_log_price"] = d.city.map(city_mean).fillna(d.state.map(state_mean))
        return x

    model = RandomForestRegressor(**RF_PARAMS).fit(features(train), log_price)
    return np.exp(model.predict(features(test)))


def gap_row(y: np.ndarray, pred: np.ndarray) -> dict:
    gap = (y - pred) / pred
    p50, p75, p90 = np.percentile(np.abs(gap), [50, 75, 90])
    return {"Median signed gap": float(np.median(gap)), "Absolute gap P50": p50, "P75": p75, "P90": p90}


def main() -> None:
    d = load_periods()
    fit, val, train, test = d["fit"], d["validation"], d["train"], d["test"]
    amenities = [c for c in train.columns if c.startswith("amenity_")]

    # --- Selection on the validation period (test data not used) -----------
    y_val = val.price.to_numpy()
    ridge_val = {a: metrics(y_val, ridge_predict(fit, val, a)) for a in RIDGE_ALPHAS}
    alpha = min(RIDGE_ALPHAS, key=lambda a: ridge_val[a]["MAPE"])
    knn_val = {}
    for k in KNN_KS:
        p, _ = knn_predict(fit, val, k)
        ok = ~np.isnan(p)
        knn_val[k] = {"Listings with a reference": ok.mean(), **metrics(y_val[ok], p[ok])}
    lowest_k = min(KNN_KS, key=lambda k: knn_val[k]["MAPE"])

    # --- Final comparison on the test data ----------------------------------
    y = test.price.to_numpy()
    knn = {k: knn_predict(train, test, k) for k in KNN_KS}
    p_knn, level = knn[config.KNN_K]
    has_ref = ~np.isnan(p_knn)
    level = np.where(has_ref, level, "none")  # too few listings even in the state
    city = level == "city"
    p_ridge_amen = ridge_predict(train, test, alpha, amenities)
    p_ridge = ridge_predict(train, test, alpha)
    p_rf = rf_predict(train, test, amenities)

    all_models = {"Naive: city median, same bedrooms": metrics(y, naive_predict(train, test))}
    for k, (p, _) in knn.items():
        ok = ~np.isnan(p)
        all_models[f"KNN, k = {k}"] = metrics(y[ok], p[ok])
    all_models["Ridge, log(price), with amenities"] = metrics(y, p_ridge_amen)
    all_models["Ridge, log(price), without amenities (system)"] = metrics(y, p_ridge)
    all_models["Random Forest, log(price)"] = metrics(y, p_rf)

    by_level = {}
    for lvl, label in (("city", "Same city"), ("state", "Same state (fallback)"), ("none", "None")):
        m = level == lvl
        row = {"Share of test listings": m.mean()}
        if lvl != "none" and m.any():
            row.update({k: v for k, v in metrics(y[m], p_knn[m]).items()
                        if k in ("MAE (USD)", "MAPE", "Within ±25%")})
        else:
            row.update({"MAE (USD)": "–", "MAPE": "–", "Within ±25%": "–"})
        by_level[label] = row

    models = {f"KNN, k = {config.KNN_K}": p_knn, "Ridge with amenities": p_ridge_amen,
              "Ridge without amenities (system)": p_ridge, "Random Forest": p_rf}
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
        f"- Training set: {len(train):,} listings posted before {TEST_FROM}",
        f"- Test set: {len(test):,} listings posted from {TEST_FROM} (December 2019)",
        f"- Test listings in a city that appears in the training set: {test.city.isin(set(train.city)).mean():.1%}",
        f"- KNN (rentwise.price): same city, widened to the state below {config.MIN_COMPARABLES} "
        f"listings; standardised {', '.join(KNN_ATTRIBUTES)}",
        f"- Ridge (rentwise.price): alpha = {alpha:g}, chosen on the validation period; "
        f"Random Forest: {RF_PARAMS['n_estimators']} trees, min_samples_leaf = {RF_PARAMS['min_samples_leaf']}",
        "",
        "## Selection on the validation period",
        "",
        f"- Fitting set: {len(fit):,} training listings posted before {VALIDATION_FROM}",
        f"- Validation period: {len(val):,} training listings posted from {VALIDATION_FROM} to before {TEST_FROM}",
        f"- Validation listings in a city that appears in the fitting set: {val.city.isin(set(fit.city)).mean():.1%}",
        "- Criterion: lowest MAPE on the validation period. The test data are not used.",
        "",
        "### Ridge without amenities, by alpha",
        "",
        md_table([(f"alpha = {a:g}" + (" (chosen)" if a == alpha else ""), m) for a, m in ridge_val.items()],
                 first="Ridge"),
        "",
        "### KNN, reference = median of the k nearest listings, by k",
        "",
        md_table([(f"k = {k}" + (" (lowest MAPE)" if k == lowest_k else ""), m) for k, m in knn_val.items()],
                 first="KNN"),
        "",
        "## All models (test set)",
        "",
        "KNN rows exclude the test listings for which no reference could be computed.",
        "",
        md_table(all_models),
        "",
        f"## KNN (k = {config.KNN_K}) by evidence level (test set)",
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
    ]
    write(OUT, out)


if __name__ == "__main__":
    main()
