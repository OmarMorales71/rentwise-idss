# RentWise IDSS

An Intelligent Decision Support System (IDSS) that helps users assess whether an apartment listing offers reasonable value and matches their personal requirements.

The user provides an apartment listing and their preferences. The system evaluates the asking rent against comparable listings, checks mandatory requirements and optional preferences, and produces an explainable recommendation:

- **Shortlist** — the apartment meets mandatory requirements and appears to offer reasonable value.
- **Review** — more information or comparable listings are needed, or some aspects require closer consideration.
- **Skip** — the apartment fails a mandatory requirement or appears to offer poor value when sufficient comparison data is available.

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
├── report/
├── README.md
├── data_and_tools_selection.md
├── pyproject.toml / uv.lock   dependencies (see Setup)
└── requirements.txt
```

Keep `dataset/raw/` unchanged: do not clean, transform, rename or overwrite the original data. To rebuild the clean data, run `uv run python scripts/clean_dataset.py`.

## Proposed methods and tools

The initial proposal is to investigate:

- **K-Nearest Neighbors (KNN):** retrieve similar apartment listings.
- **Regression models:** estimate an expected asking rent; compare a simple baseline with models such as Random Forest.
- **Weighted Sum Model (WSM):** combine the user's optional preferences.
- **Rule-based checks:** enforce mandatory requirements such as maximum budget or minimum bedrooms.
- **Python, Pandas, NumPy and Scikit-learn:** data preparation and modelling.
- **Streamlit:** prototype user interface.

These are proposed choices and should be validated against the dataset during exploration.

## Documentation

See [`data_and_tools_selection.md`](data_and_tools_selection.md) for the data, expert-knowledge research areas, proposed methods and tool selection.
