# RentWise IDSS

An Intelligent Decision Support System (IDSS) that helps users assess whether an apartment listing offers reasonable value and matches their personal preferences.

The user provides an apartment listing they have found and their preferences. Each preference (budget, size, bedrooms, bathrooms, amenities, pet policy) has a target value and an importance weight between 0 and 1; a weight of 1.0 marks it as non-negotiable. The system evaluates the asking rent against comparable listings, measures how well the listing satisfies the weighted preferences, and produces an explainable recommendation:

- **Shortlist** — no non-negotiable preference fails, the weighted personal fit is good and the apartment appears to offer reasonable value.
- **Review** — more information or comparable listings are needed (for example, a non-negotiable preference cannot be verified from the listing), or the price or fit assessment is intermediate.
- **Skip** — the apartment fails a non-negotiable preference, has a very low personal fit, or appears to offer poor value when sufficient comparison data is available.

## Setup (uv)
*I (lars) preferably use uv. The same setup can be done using other tools like pip or conda*

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (e.g. `brew install uv`).
2. In the repo root run `uv sync`. This creates `.venv/` with Python 3.12 and all dependencies from `pyproject.toml` / `uv.lock`.
3. Run code with `uv run python scripts/clean_dataset.py`, or select `.venv` as the kernel/interpreter in VS Code for the notebooks.
4. Add a package with `uv add <package>` (commit `pyproject.toml` and `uv.lock`).

## Dataset

The project uses the **Apartment for Rent Classified** dataset from the UCI Machine Learning Repository:

- Dataset page: https://archive.ics.uci.edu/dataset/555/apartment
- Dataset ID: 555
- Geographic scope: United States
- Data period: historical rental listings from 2019

The dataset includes listing attributes such as rent, square footage, bedrooms, bathrooms, location and amenities. The exact files and version used, the cleaning steps and a summary of the clean data are in [`dataset/README.md`](dataset/README.md).

**Important limitation:** The dataset contains historical asking rents, not current market rents or confirmed final rental prices. Any estimate produced by this project should be interpreted in the context of the dataset's coverage and time period.

## Repository structure

```text
rentwise-idss/
├── dataset/
│   ├── raw/               original UCI files, never modified
│   ├── processed/         clean data and raw vs clean report
│   └── README.md          source, cleaning steps and clean data summary
├── notebooks/
│   └── 01_eda_preprocessing.ipynb   exploratory analysis of raw and clean data
├── scripts/
│   └── clean_dataset.py   builds dataset/processed/ from dataset/raw/
├── rentwise/              knowledge-based component (Task 6)
│   ├── config.py          all tolerance bands and thresholds (initial values, tune in Task 7)
│   ├── preferences.py     Listing and Preference data structures, criterion names
│   ├── fit.py             satisfaction functions, Weighted Sum Model, veto
│   ├── price.py           PriceAssessment / PriceAssessor interface + placeholder assessor
│   ├── rules.py           recommendation rules R1–R4 and their reasons
│   ├── assess.py          assess(listing, preferences, price_assessor) entry point
│   └── data.py            loads the clean CSV with the right dtypes
├── app/
│   └── streamlit_app.py   Streamlit user interface (Task 8)
├── tests/                 pytest tests of the knowledge-based component
├── report/
├── README.md
├── data_and_tools_selection.md
├── pyproject.toml / uv.lock   dependencies (see Setup)
└── requirements.txt
```

Keep `dataset/raw/` unchanged: do not clean, transform, rename or overwrite the original data. To rebuild the clean data, run `uv run python scripts/clean_dataset.py`.

## Running the prototype

```bash
uv sync                                          # install dependencies
uv run python scripts/clean_dataset.py           # only if dataset/processed/apartments_clean.csv is missing
uv run streamlit run app/streamlit_app.py        # start the user interface
uv run pytest                                    # run the tests
```

The app opens at http://localhost:8501. Pick an example preset in the sidebar (Shortlist, Review, Skip) or enter your own listing and preferences.

From Python, the whole assessment is one call:

```python
from rentwise import assess, Listing, Preference, RidgeKnnPriceAssessor
from rentwise.data import load_listings

listing = Listing(price=1200, square_feet=950, bedrooms=2, bathrooms=2.0,
                  cityname="Houston", state="TX", amenities={"amenity_parking"},
                  cats_allowed=True, dogs_allowed=None)
prefs = [Preference("budget", 1400, 0.8), Preference("dogs", weight=1.0)]
result = assess(listing, prefs, RidgeKnnPriceAssessor(load_listings()))
print(result.recommendation, result.reasons)
```

`RidgeKnnPriceAssessor` (`rentwise/price.py`) is the price assessment A1 (report, Chapter 5): Ridge regression on log(price) estimates the reference rent, and KNN retrieves the 10 most similar listings (same city, or the state if the city has fewer than 10) and judges whether the evidence is sufficient (10 comparables and mean distance at most `MAX_MEAN_DISTANCE`). Any class with `assess(listing) -> PriceAssessment` can replace it (the `PriceAssessor` protocol).

## Proposed methods and tools

The initial proposal is to investigate:

- **K-Nearest Neighbors (KNN):** retrieve similar apartment listings.
- **Regression models:** estimate an expected asking rent; compare a simple baseline with models such as Random Forest.
- **Weighted Sum Model (WSM):** combine the user's weighted preferences into a personal-fit score. Each preference is satisfied to a degree between 0 and 1 (for example, satisfaction decreases gradually as the rent exceeds the budget), so a small shortfall on one preference can be offset by others.
- **Rule-based checks:** apply the veto of non-negotiable preferences (weight 1.0) and the rules that turn price position and personal fit into a recommendation. Preferences the listing does not state (such as an unstated pet policy) are excluded from the score and flagged instead of counted as failed.
- **Python, Pandas, NumPy and Scikit-learn:** data preparation and modelling.
- **Streamlit:** prototype user interface.

These are proposed choices and should be validated against the dataset during exploration.

## Documentation

See [`data_and_tools_selection.md`](data_and_tools_selection.md) for the data, expert-knowledge research areas, proposed methods and tool selection.
