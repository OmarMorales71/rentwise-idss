"""Calibrate the parameters of the IDSS on the validation period.

Usage (from the repository root, after scripts/clean_dataset.py):

    uv run python scripts/calibrate_parameters.py

Writes  results/calibration.md

Every choice is made on the validation period (September-November 2019), with
the price models fitted on the fitting set (before September 2019). The test
set is not read. The criteria are explained in report/validation_criteria.md:

1. d_max  = 95th percentile of the mean distance of the comparables.
2. b1, b2 = 50th and 90th percentiles of the absolute gap |asking - reference| / reference,
            over the validation listings with sufficient evidence.
3. Knowledge-based parameters: one-at-a-time sensitivity analysis on simulated
   renters. A value is kept when Review stays at most REVIEW_MAX of the
   assessments and moving to an adjacent grid value changes the class of at
   most FLIP_MAX of them.

The selected values must then be copied into rentwise/config.py.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from _common import RESULTS, VALIDATION_FROM, load_periods, md_table, write
from _renters import simulate
from rentwise import config
from rentwise.fit import personal_fit
from rentwise.price import PriceAssessment, RidgeKnnPriceAssessor
from rentwise.rules import recommend

OUT = RESULTS / "calibration.md"
D_MAX_PERCENTILE = 95
BAND_PERCENTILES = (50, 90)
REVIEW_MAX = 0.50
FLIP_MAX = 0.10
N_RENTERS = 10_000
INITIAL_BANDS = (0.10, 0.25)  # price bands set by the team before calibration

GRIDS = {
    "BUDGET_TOLERANCE": [0.10, 0.15, 0.20, 0.25, 0.30],
    "SQUARE_FEET_TOLERANCE": [0.15, 0.20, 0.25, 0.30, 0.35],
    "BEDROOMS_BAND": [1.0, 1.5, 2.0, 2.5, 3.0],
    "BATHROOMS_BAND": [0.5, 0.75, 1.0, 1.25, 1.5],
    "FIT_VERY_LOW": [0.30, 0.35, 0.40, 0.45, 0.50],
    "FIT_GOOD": [0.60, 0.65, 0.70, 0.75, 0.80],
}


def ceil2(x: float) -> float:
    return math.ceil(x * 100) / 100


def round2(x: float) -> float:
    return round(x, 2)


def price_assessments(a1: pd.DataFrame) -> list[PriceAssessment]:
    """Turn the rows of assess_frame into the PriceAssessment used by the rules."""
    return [PriceAssessment(r.reference, r.position, int(r.n_comparables),
                            bool(r.evidence_sufficient),
                            mean_distance=None if np.isnan(r.mean_distance) else r.mean_distance)
            for r in a1.itertuples()]


def classify(pairs, prices) -> tuple[np.ndarray, np.ndarray]:
    classes, rules = [], []
    for (listing, prefs), price in zip(pairs, prices):
        rec, rule, _ = recommend(personal_fit(listing, prefs), price, listing.price)
        classes.append(rec)
        rules.append(rule)
    return np.array(classes), np.array(rules)


def shares(classes: np.ndarray, rules: np.ndarray) -> dict:
    row = {c: float(np.mean(classes == c)) for c in ("Shortlist", "Review", "Skip")}
    row.update({r: float(np.mean(rules == r)) for r in ("R1", "R2", "R3", "R4")})
    return row


def main() -> None:
    d = load_periods()
    fit, val = d["fit"], d["validation"]
    assessor = RidgeKnnPriceAssessor(fit, max_mean_distance=np.inf)
    raw = assessor.assess_frame(val)
    ape = np.abs(val.price.to_numpy() - raw.reference.to_numpy()) / val.price.to_numpy()

    # --- 1. d_max -------------------------------------------------------------
    full = raw.n_comparables >= config.KNN_K
    d_max = ceil2(np.percentile(raw.mean_distance[full], D_MAX_PERCENTILE))
    deciles = pd.qcut(raw.mean_distance[full], 10, duplicates="drop")
    by_decile = [(str(interval), {"Listings": int(m.sum()), "Ridge MAPE": float(ape[full][m].mean())})
                 for interval, m in ((iv, (deciles == iv).to_numpy()) for iv in deciles.cat.categories)]

    # --- 2. price bands -------------------------------------------------------
    sufficient = full & (raw.mean_distance <= d_max)
    gap = raw.gap[sufficient].to_numpy()
    b1, b2 = (round2(np.percentile(np.abs(gap), p)) for p in BAND_PERCENTILES)
    gap_pct = {f"P{p}": float(np.percentile(np.abs(gap), p)) for p in (25, 50, 75, 90, 95)}

    def positions(in_line: float, moderate: float) -> dict:
        return {"Below": float(np.mean(gap < -in_line)),
                "In line": float(np.mean(np.abs(gap) <= in_line)),
                "Moderately above": float(np.mean((gap > in_line) & (gap <= moderate))),
                "Significantly above": float(np.mean(gap > moderate))}

    band_rows = [(f"Initial (±{INITIAL_BANDS[0]:.0%}, +{INITIAL_BANDS[1]:.0%})",
                  positions(*INITIAL_BANDS)),
                 (f"Calibrated (±{b1:.0%}, +{b2:.0%})", positions(b1, b2))]

    # Apply the calibrated price parameters before studying the knowledge base.
    config.MAX_MEAN_DISTANCE, config.IN_LINE_BAND, config.MODERATE_BAND = d_max, b1, b2

    # --- 3. knowledge-based parameters ----------------------------------------
    sample = val.sample(N_RENTERS, random_state=0)
    pairs = simulate(sample, reference=fit)
    a1 = RidgeKnnPriceAssessor(fit).assess_frame(sample)
    prices = price_assessments(a1)
    base_classes, base_rules = classify(pairs, prices)
    baseline = shares(base_classes, base_rules)

    sensitivity, decisions = {}, []
    for name, grid in GRIDS.items():
        initial = getattr(config, name)
        rows, results = [], {}
        for value in grid:
            setattr(config, name, value)
            classes, rules = classify(pairs, prices)
            results[value] = classes
            rows.append((f"{value:g}" + (" (initial)" if value == initial else ""),
                         {**shares(classes, rules),
                          "Changed class": float(np.mean(classes != base_classes))}))
        setattr(config, name, initial)

        def ok(i: int) -> bool:
            review = float(np.mean(results[grid[i]] == "Review"))
            flips = [float(np.mean(results[grid[i]] != results[grid[j]]))
                     for j in (i - 1, i + 1) if 0 <= j < len(grid)]
            return review <= REVIEW_MAX and max(flips) <= FLIP_MAX

        i0 = grid.index(initial)
        candidates = sorted(range(len(grid)), key=lambda i: (abs(i - i0), i))
        chosen = next((grid[i] for i in candidates if ok(i)), None)
        decisions.append((name, {"Initial": f"{initial:g}",
                                 "Initial meets criteria": "yes" if ok(i0) else "no",
                                 "Selected": "keep initial (no value meets the criteria)"
                                 if chosen is None else f"{chosen:g}"}))
        sensitivity[name] = rows

    out = [
        "# Calibration of the IDSS parameters (validation period)",
        "",
        "Generated by `scripts/calibrate_parameters.py`. Do not edit by hand.",
        "Criteria: `report/validation_criteria.md`. Copy the selected values into `rentwise/config.py`.",
        "",
        f"- Fitting set: {len(fit):,} listings posted before {VALIDATION_FROM}",
        f"- Validation period: {len(val):,} listings (September-November 2019); the test set is not read",
        f"- Price models: Ridge alpha = {config.RIDGE_ALPHA:g}, KNN k = {config.KNN_K}",
        "",
        "## 1. Maximum mean distance of the comparables (d_max)",
        "",
        f"Validation listings with {config.KNN_K} comparables: {full.mean():.1%} "
        f"(city level {np.mean(raw.level[full] == 'city'):.1%}, state level {np.mean(raw.level[full] == 'state'):.1%}).",
        "",
        f"**d_max = P{D_MAX_PERCENTILE} of the mean distance = {d_max:.2f}** "
        f"(rounded up to two decimals). Listings above it: {np.mean(raw.mean_distance[full] > d_max):.1%}.",
        "",
        "Ridge error by decile of the mean distance:",
        "",
        md_table(by_decile, first="Mean distance"),
        "",
        "## 2. Price bands (b1, b2)",
        "",
        f"Gap = (asking - reference) / reference, over the {int(sufficient.sum()):,} validation "
        "listings with sufficient evidence.",
        "",
        md_table({"Absolute gap": gap_pct}, first="Percentile"),
        "",
        f"- Median signed gap: {np.median(gap):+.1%}",
        f"- **b1 = P{BAND_PERCENTILES[0]} = {b1:.2f}** (in line: -b1 <= gap <= b1)",
        f"- **b2 = P{BAND_PERCENTILES[1]} = {b2:.2f}** (significantly above: gap > b2)",
        "",
        "Price positions of the validation listings with sufficient evidence:",
        "",
        md_table(band_rows, first="Bands"),
        "",
        "## 3. Knowledge-based parameters (sensitivity analysis)",
        "",
        f"- {N_RENTERS:,} validation listings, one simulated renter each (`scripts/_renters.py`, seed fixed)",
        f"- Price parameters as calibrated above (d_max = {d_max:.2f}, b1 = {b1:.2f}, b2 = {b2:.2f})",
        f"- Criteria: Review at most {REVIEW_MAX:.0%} of the assessments, and at most {FLIP_MAX:.0%} "
        "of the assessments change class when the parameter moves to an adjacent grid value",
        "- One parameter varies at a time; the others keep their initial values",
        "",
        "### Baseline (all initial values)",
        "",
        md_table({"Baseline": baseline}, first="Values"),
        "",
        "### Selected values",
        "",
        md_table(decisions, first="Parameter"),
        "",
    ]
    for name, rows in sensitivity.items():
        out += [f"### {name}", "", md_table(rows, first="Value"), ""]
    write(OUT, out)


if __name__ == "__main__":
    main()
