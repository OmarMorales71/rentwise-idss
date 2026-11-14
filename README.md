# RentWise IDSS

An Intelligent Decision Support System (IDSS) that helps users assess whether an apartment listing offers reasonable value and matches their personal requirements.

The user provides an apartment listing and their preferences. The system evaluates the asking rent against comparable listings, checks mandatory requirements and optional preferences, and produces an explainable recommendation:

- **Shortlist** — the apartment meets mandatory requirements and appears to offer reasonable value.
- **Review** — more information or comparable listings are needed, or some aspects require closer consideration.
- **Skip** — the apartment fails a mandatory requirement or appears to offer poor value when sufficient comparison data is available.

## Dataset

The project uses the **Apartment for Rent Classified** dataset from the UCI Machine Learning Repository:

- Dataset page: https://archive.ics.uci.edu/dataset/555/apartment
- Dataset ID: 555
- Geographic scope: United States
- Data period: historical rental listings from 2019

The dataset includes listing attributes such as rent, square footage, bedrooms, bathrooms, location and amenities. The exact files and version used by the team should be recorded in `data/raw/README.md`.

**Important limitation:** The dataset contains historical asking rents, not current market rents or confirmed final rental prices. Any estimate produced by this project should be interpreted in the context of the dataset's coverage and time period.

## Repository structure

```text
rentwise-idss/
├── data/
│   └── raw/
│       └── README.md
├── README.md
└── data_and_tools_selection.md
```

Place the original dataset files in `data/raw/`. Keep this folder unchanged: do not clean, transform, rename or overwrite the original data. Processed data and analysis outputs should be stored separately in later project stages.

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
