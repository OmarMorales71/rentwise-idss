# Data preprocessing: steps taken

Source: UCI *Apartment for Rent Classified* (id 555), file `apartments_for_rent_classified_100K.csv` (99,492 rows, 22 columns, US listings Dec 2018 – Dec 2019). Code: `src/preprocessing.py`; exploration: `notebooks/01_eda_preprocessing.ipynb`.

1. **Load** the raw CSV unchanged (`;`-separated, cp1252 encoding; UTF-8 fails).
2. **Exact duplicates:** dropped 84 identical rows.
3. **Reposts:** dropped 755 listings with the same description, price, size, rooms and coordinates as another listing (same unit re-posted seconds apart under a different title); kept the latest. Listings that only share attributes are kept (identical units in one building).
4. **Category:** kept only `housing/rent/apartment` (−61: retail, short-term, homes, condos).
5. **Price type:** kept monthly prices only (−4 weekly).
6. **Missing core values:** dropped rows without price, bedrooms or bathrooms (−183).
7. **Location:** dropped rows without city/state/coordinates or with the US-centroid placeholder coordinates 39.8163, −98.5576 (−298).
8. **Plausibility / scope:** kept price 300–10,000 USD, 150–5,000 sq ft and 0.25–10 USD per sq ft (−111; low end = weekly rates/errors, high end = luxury estates outside our use case).
9. **Feature preparation (no rows removed):**
   - amenities string → 27 binary `amenity_*` columns + `n_amenities`;
   - `pets_allowed` → `pets_cats`, `pets_dogs`;
   - `pets_unknown`, `amenities_unknown` flags (missing ≠ absent, so no imputation);
   - `has_photo` → binary; `time` → `listed_at` datetime; derived `price_per_sqft`;
   - dropped text/constant columns: title, body, address (92% missing), price_display, currency (all USD), fee, category, price_type.
10. **Output:** `data/processed/apartments_clean.csv` — 97,996 rows, 45 columns (98.5% of raw rows kept).

The data are 2019 asking rents, not current or agreed prices.
