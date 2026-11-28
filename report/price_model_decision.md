# Price assessment (A1): from KNN to regression + KNN

This note explains why the price assessment (A1) changes from a KNN-only approach to a regression model combined with KNN, and reports the test that supports the change.

The test is reproducible: `scripts/compare_price_models.py` (run after `scripts/clean_dataset.py`) recomputes every number below and writes them to `results/price_model_comparison.md`.

## 1. Previous approach

Chapters 2 and 3 described A1 as follows:

1. KNN retrieves the 10 historical listings most similar to the one under assessment (same city, similar floor area, bedrooms and bathrooms).
2. If there are too few comparable listings, no price judgement is issued.
3. The reference asking rent is the median price of those comparable listings.
4. The reference is "complemented by a regression estimate if it proves reliable during validation".

Two problems:

- Point 4 is imprecise. It names a regression model but does not say what it does or when it is used. This is the kind of vagueness the professor criticised ("nor decided precisely which data-driven models … will be implemented").
- The test below shows that the median of the comparable listings is a less accurate reference than a regression model.

## 2. New approach

A1 splits its work between two models, each used for what it does best.

| Task in A1 | Done by | Why |
|---|---|---|
| Estimate the reference asking rent | Ridge regression on log(price) | Most accurate reference (see results) |
| Retrieve the comparable listings shown to the renter | KNN | Real listings the renter can inspect |
| Decide whether the evidence is sufficient | KNN (enough similar listings in the city?) | Easy to explain; prevents a judgement on weak data |
| Comparison model in the report | Random Forest | Shows that Ridge was chosen against a stronger, non-linear alternative |

Ridge uses the same inputs that the report already lists for A1: location (city and state), floor area, bedrooms and bathrooms. It does not use amenities (see section 4.4).

### Example

A renter assesses a listing in Austin, TX: 2 bedrooms, 1 bathroom, 850 sq ft, asking 1,750 USD per month (illustrative numbers).

1. KNN finds the 10 most similar listings in Austin. There are enough, so the evidence is sufficient. The 10 listings are kept to show to the renter.
2. Ridge estimates the reference asking rent for this listing: 1,500 USD.
3. The asking rent is 17% above the reference, so it is placed in one of the four positions (below, in line, moderately above, significantly above) according to the bands calibrated in validation.
4. The renter sees: "Estimated reference rent: 1,500 USD (+17%). Based on listings like yours in Austin; the 10 most similar are: …".

If KNN does not find enough comparable listings (for example, a city with two listings), no price judgement is issued, even though Ridge could produce a number. The rule of Chapter 2 is kept: without sufficient evidence, the IDSS does not judge the price.

One consequence to accept: the reference (1,500) does not have to equal the median of the 10 listings shown. The interface therefore says "based on listings like yours", not "the median of these listings".

## 3. Test setup

- Data: `dataset/processed/apartments_clean.csv` (87,452 listings), produced by `scripts/clean_dataset.py`.
- Temporal split, which mimics real use (the system assesses listings newer than its data):
  - Train: 80,311 listings posted before December 2019.
  - Test: 7,141 listings posted in December 2019 (the last collection period).
  - 87.8% of the test listings are in a city that also appears in the training data.
- Models:
  - Naive baseline: median price in the same city with the same number of bedrooms (falls back to the city, then the state).
  - KNN: candidates from the same city, widened to the state when the city has fewer than 10 listings; distance on standardised floor area, bedrooms and bathrooms; reference = median price of the k nearest listings; k = 5, 10, 20.
  - Ridge (alpha = 1, chosen on the validation period) on log(price): standardised log floor area, bedrooms and bathrooms, plus one-hot city and state; tested with and without the 27 amenity indicators.
  - Random Forest (200 trees, min_samples_leaf = 3) on log(price): floor area, bedrooms, bathrooms, coordinates, state, city mean log price (computed on the training data only), and amenities.
- Metrics on the test listings: MAE (USD), MAPE, median absolute percentage error (MdAPE), and the share of listings whose asking rent is within ±10% and ±25% of the predicted reference.
- Selection: the Ridge alpha (nine values, 0.01 to 100) and the KNN k (5, 10, 20) are chosen on a validation period inside the training data (fit on listings before September 2019, validate on September–November 2019), by lowest MAPE. alpha = 1 is selected; k = 10 is kept (the three values differ by less than one point of MAPE). The test data are not used for any choice. Random Forest settings are not tuned.

## 4. Results

### 4.1 All models

| Model | MAE (USD) | MAPE | MdAPE | Within ±10% | Within ±25% |
|---|---|---|---|---|---|
| Naive: city median, same bedrooms | 396 | 26.7% | 19.9% | 28.8% | 59.2% |
| KNN, k = 5 | 350 | 23.8% | 17.6% | 32.1% | 65.2% |
| KNN, k = 10 | 348 | 23.3% | 17.3% | 31.9% | 65.5% |
| KNN, k = 20 | 356 | 23.6% | 17.8% | 30.9% | 64.6% |
| Ridge, log(price), with amenities | 270 | 17.6% | 14.0% | 36.9% | 75.8% |
| Random Forest, log(price) | 292 | 19.1% | 14.5% | 37.3% | 72.7% |

KNN rows exclude the 0.3% of test listings for which no reference could be computed (fewer than 10 listings in the state).

Ridge is the most accurate model: about 80 USD less error per listing than KNN and 5.7 percentage points lower MAPE. Random Forest is in between. The choice of k barely matters for KNN; k = 10 is the best.

### 4.2 KNN by evidence level (k = 10)

| Comparables found in | Share of test listings | MAE (USD) | MAPE | Within ±25% |
|---|---|---|---|---|
| Same city | 68.4% | 333 | 21.0% | 68.0% |
| Same state (fallback) | 31.2% | 380 | 28.3% | 59.9% |
| None | 0.3% | – | – | – |

KNN is clearly worse when it has to widen the search to the state, which happens for almost a third of the test listings.

### 4.3 Same listings only (city-level evidence)

To compare the models on the cases where KNN is at its best, only the 4,886 test listings with comparable listings in their own city:

| Model | MAE (USD) | MAPE | MdAPE | Within ±10% | Within ±25% |
|---|---|---|---|---|---|
| KNN, k = 10 | 333 | 21.0% | 16.1% | 34.4% | 68.0% |
| Random Forest | 284 | 17.6% | 13.9% | 39.0% | 74.7% |
| Ridge, with amenities | 267 | 16.7% | 13.5% | 38.3% | 77.3% |

Ridge remains better even where KNN has local evidence.

### 4.4 Ridge with and without amenities

The report states that A1 uses location, floor area, bedrooms and bathrooms. Amenities are also problematic as inputs: 16.6% of the listings give no amenity list, which the model would read as "no amenities". Ridge was therefore tested without them.

| Model | Rows | MAE (USD) | MAPE | MdAPE | Within ±10% | Within ±25% |
|---|---|---|---|---|---|---|
| KNN, k = 10 | all | 348 | 23.3% | 17.3% | 31.9% | 65.5% |
| Ridge with amenities | all | 271 | 17.6% | 14.0% | 37.0% | 75.8% |
| Ridge without amenities | all | 271 | 17.9% | 14.2% | 37.2% | 74.8% |
| KNN, k = 10 | city level | 333 | 21.0% | 16.1% | 34.4% | 68.0% |
| Ridge with amenities | city level | 267 | 16.7% | 13.5% | 38.3% | 77.3% |
| Ridge without amenities | city level | 268 | 17.2% | 13.7% | 38.2% | 76.4% |

("All" here means the test listings for which KNN found a reference, so that all rows use the same listings.)

Dropping amenities costs almost nothing (same MAE, +0.3 points of MAPE) and keeps A1 consistent with the report. Ridge without amenities is the chosen model.

### 4.5 Bias and spread of the gap

Gap = (asking rent − reference) / reference, on the city-level test listings.

| Model | Median signed gap | Absolute gap P50 | P75 | P90 |
|---|---|---|---|---|
| KNN, k = 10 | +4.2% | 16.3% | 31.7% | 55.2% |
| Ridge, with amenities | +4.8% | 13.9% | 25.0% | 41.8% |
| Ridge, without amenities (chosen) | +2.7% | 13.8% | 25.1% | 41.6% |
| Random Forest | +5.5% | 14.1% | 26.9% | 47.6% |

Two observations:

- All models under-estimate December 2019, by about 3–5%. This is price drift over time, not a weakness of one model: the reference is built from older listings. It should be reported in the validation chapter.
- The gap between real asking rents and any reference is wide: even with Ridge, half of the listings deviate by more than 14% and one in ten by more than 42%. The current bands in `rentwise/config.py` (in line within ±10%, significantly above beyond +25%) are too narrow and would mark many ordinary listings as overpriced. The bands must be calibrated on this distribution, as Chapter 2 already states.

## 5. Decision

- Reference asking rent: Ridge regression on log(price), with city and state, floor area, bedrooms and bathrooms.
- Comparable listings and evidence sufficiency: KNN (k = 10), same city, widened to the state when the city has fewer than 10 listings.
- Comparison model: Random Forest.
- Price bands: calibrated from the distribution of the gap between asking rents and the Ridge reference.

## 6. Changes in the report

| Chapter | Change |
|---|---|
| 1 | None. |
| 2 | "Establishing a reference asking rent": the reference is estimated by a regression model trained on the prepared listings; the comparable listings support it as evidence and are shown to the renter. |
| 3 | Analysis, A1 paragraph: same change. Architecture figure: A1 label "data-driven (KNN comparables)" becomes "data-driven (regression + KNN comparables)". |
| 4 | The prepared listings are also used to train the regression model. New "Modelling Dataset" section: target log(price), inputs, standardisation, temporal split. |
| 5 | Model 1: Ridge (reference). KNN: comparable listings and evidence. Model 2: Random Forest (comparison). |
| 6 | Results of this comparison, the temporal drift, and the calibration of the price bands and of the minimum number of comparable listings. |
| 7 | "Interaction with Data-driven Models" currently describes the placeholder assessor and must be updated. |

The influence diagram does not change: the arc "Comparable evidence → Price position" still holds, since both the reference and the comparable listings come from the same historical data.

## 7. Limitations of the test

- A single temporal split. Ridge alpha and KNN k are selected on a validation period; KNN features and weighting and the Random Forest settings are not tuned. An improved KNN, for example with distance weighting, could narrow the gap, but is unlikely to overtake Ridge.
- The results depend on the temporal split chosen in `scripts/compare_price_models.py` (test = December 2019). Chapter 6 should report them together with this choice.
