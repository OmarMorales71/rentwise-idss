# Gather Data and Expert Knowledge, Choose the Tools

## 1. Project overview

The project aims to develop an Intelligent Decision Support System (IDSS) that helps a user decide whether an apartment listing is reasonably priced and matches their personal preferences.

The user will enter an apartment they have already found, together with their preferences. The system will assess the asking rent, compare the listing with similar apartments, evaluate the user's weighted preferences and provide an explainable recommendation: **Shortlist, Review or Skip**.

## 2. Data collection

The primary data source is the [UCI Apartment for Rent Classified dataset](https://archive.ics.uci.edu/dataset/555/apartment).

Relevant attributes include:

- Asking rent.
- Square footage.
- Number of bedrooms and bathrooms.
- City, state and geographic coordinates.
- Amenities and other listing characteristics.

The team will inspect the dataset structure and assess missing values, duplicates, inconsistent values, outliers and the distribution of listings across cities.

The raw source files will be stored unchanged in `data/raw/`. Any cleaning, feature engineering or transformations will be performed on separate copies.

**Data limitation:** The dataset contains historical US rental listings from 2019. It represents advertised asking rents, not necessarily agreed rental prices, and should not be treated as a source of current market prices.

## 3. Expert knowledge

The project will use domain knowledge from real-estate valuation and decision-analysis research.

The main topics to investigate are:

- **Comparable properties:** how similar listings are selected to assess an asking rent.
- **Rental price factors:** how location, size, bedrooms, bathrooms and amenities relate to asking rent.
- **User preferences:** how to weight criteria by importance, how to measure partial satisfaction (for example, a rent slightly above budget) and when a criterion should be non-negotiable.
- **Multi-criteria decision-making:** how different preferences can be combined transparently.
- **Decision explanations:** how to communicate the factors behind a recommendation and identify when there is insufficient evidence.

Potential sources include academic literature on rental-price estimation, real-estate valuation and multi-criteria decision analysis.

## 4. Proposed tools and methods

| Tool or method | Purpose |
|---|---|
| Python | Main programming language |
| Pandas and NumPy | Data inspection, cleaning and preparation |
| Matplotlib / Seaborn | Exploratory data analysis and visualisation |
| Scikit-learn | Similarity search and predictive modelling |
| K-Nearest Neighbors (KNN) | Retrieve comparable apartment listings |
| Regression models | Estimate an expected asking rent; compare a baseline with models such as Random Forest |
| Weighted Sum Model (WSM) | Combine weighted user preferences into a personal-fit score |
| Rule-based checks | Veto non-negotiable preferences and combine price and fit into a recommendation |
| Streamlit | Build a prototype user interface |

These are initial choices to be evaluated during development. The final model will depend on data quality, the number of comparable listings available per city and model evaluation results.

## 5. Decision approach

The system will produce two separate assessments before generating its final recommendation.

### Price assessment

The entered listing will be compared with similar listings, preferably in the same city and, where possible, nearby areas. A regression model may provide an additional estimated asking rent. The system will show the available comparable examples and communicate uncertainty when there are too few suitable matches.

### Personal-fit assessment

The user states a target value and an importance weight (0 to 1) for each criterion that matters to them, for example:

- Monthly budget (e.g. 2,000 USD with weight 0.7).
- Square footage.
- Number of bedrooms and bathrooms.
- Amenities such as parking, washer and dryer, gym or pool.
- Pet policy.

Each criterion is satisfied to a degree between 0 and 1 rather than pass/fail. For the budget, satisfaction is 1 when the rent is within the budget and decreases gradually as the rent exceeds it, reaching 0 at the end of a tolerance band; size, bedrooms and bathrooms are treated the same way. The degrees of satisfaction are combined with the weights using a Weighted Sum Model, so a listing slightly above budget can still fit well if it is strong on the other criteria.

A weight of 1.0 marks a criterion as non-negotiable: if the listing does not satisfy it, the listing is skipped whatever its score (veto). Criteria that the listing does not state, such as an unstated pet policy, are excluded from the score and flagged in the explanation; an unverifiable non-negotiable criterion leads to Review, not Skip.

The width of the tolerance bands and the score thresholds are system parameters to be defined and tested during development.

### Final recommendation

- **Shortlist:** no non-negotiable criterion fails, the weighted personal fit is good and the asking rent appears reasonable relative to available comparables.
- **Review:** evidence is limited, a non-negotiable criterion cannot be verified from the listing, or the price/fit assessment is intermediate.
- **Skip:** a non-negotiable criterion is not met, the weighted personal fit is very low, or the listing appears significantly overpriced based on sufficient comparable evidence.

The recommendation will include the reasons behind the result. A lack of comparable data should lead to an uncertainty warning rather than an unsupported price judgement.
