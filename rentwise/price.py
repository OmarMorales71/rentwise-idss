"""Price assessment (A1): the data-driven component (report, Chapter 5).

A1 combines two models, each used for what it does best:

- KNN retrieves the k most similar listings (same city, widened to the state
  when the city has fewer than MIN_COMPARABLES listings) and judges whether the
  evidence is sufficient: n >= k and mean distance <= MAX_MEAN_DISTANCE.
- Ridge regression on log(price) estimates the reference asking rent from the
  standardised log floor area, bedrooms and bathrooms and one-hot city and state.

When the evidence is insufficient no price position is issued, although the
Ridge reference is still returned as indicative information.

The knowledge-based component only needs a `PriceAssessment`. Any object with
an `assess(listing) -> PriceAssessment` method can provide it (see the
`PriceAssessor` protocol), which lets the tests use simple stubs.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from rentwise import config
from rentwise.preferences import Listing

Position = Literal["below", "in_line", "moderately_above", "significantly_above"]
EvidenceLevel = Literal["city", "state", "none"]

# Attributes compared by KNN and used as numeric inputs by Ridge (report, 4.5).
KNN_ATTRIBUTES = ["square_feet", "bedrooms", "bathrooms"]


@dataclass
class PriceAssessment:
    """Output of a price assessor (report, Table 2.2, A1).

    reference_rent: reference asking rent in 2018-2019 USD per month (None if no
        reference can be produced).
    position: price position of the asking rent; None when the evidence is
        insufficient, because then no price judgement is made.
    n_comparables: number of comparable listings found.
    evidence_sufficient: True when there is enough evidence for a judgement.
    comparables: the comparable listings used, closest first.
    method: short description of how the reference was obtained (for the UI).
    level: where the comparables were found: "city", "state" or "none".
    mean_distance: mean standardised distance of the comparables to the listing.
    """

    reference_rent: float | None
    position: Position | None
    n_comparables: int
    evidence_sufficient: bool
    comparables: pd.DataFrame = field(default_factory=pd.DataFrame)
    method: str = ""
    level: EvidenceLevel = "none"
    mean_distance: float | None = None

    def gap(self, asking_rent: float) -> float | None:
        """Relative gap (asking - reference) / reference, e.g. 0.15 = 15% above."""
        if not self.reference_rent:
            return None
        return (asking_rent - self.reference_rent) / self.reference_rent


class PriceAssessor(Protocol):
    """What the knowledge-based component expects from the data-driven model."""

    def assess(self, listing: Listing) -> PriceAssessment: ...


def price_position(asking_rent: float, reference_rent: float) -> Position:
    """Place the asking rent relative to the reference (bands in config.py)."""
    gap = (asking_rent - reference_rent) / reference_rent
    if gap < -config.IN_LINE_BAND:
        return "below"
    if gap <= config.IN_LINE_BAND:
        return "in_line"
    if gap <= config.MODERATE_BAND:
        return "moderately_above"
    return "significantly_above"


def _city_key(cityname: pd.Series | str, state: pd.Series | str):
    """City names repeat across states (Austin, TX vs Austin, MN): key on both."""
    return cityname + ", " + state


def _log_floor_area(x: pd.DataFrame) -> pd.DataFrame:
    return x.assign(square_feet=np.log(x["square_feet"]))


def build_reference_model(alpha: float = config.RIDGE_ALPHA) -> Pipeline:
    """Ridge on log(price): standardised log floor area, bedrooms and bathrooms,
    and one-hot city and state. An unseen city gets all city indicators at zero,
    so its estimate rests on the state and the size of the apartment."""
    numeric = make_pipeline(
        FunctionTransformer(_log_floor_area, feature_names_out="one-to-one"),
        StandardScaler(),
    )
    features = ColumnTransformer([
        ("numeric", numeric, KNN_ATTRIBUTES),
        ("location", OneHotEncoder(handle_unknown="ignore"), ["city", "state"]),
    ])
    return Pipeline([("features", features), ("ridge", Ridge(alpha=alpha))])


class RidgeKnnPriceAssessor:
    """Price assessment A1: Ridge reference + KNN comparables and evidence.

    Fitted once on the prepared listings; each `assess` call then needs one
    nearest-neighbour search within a city or state and one Ridge prediction.
    """

    def __init__(self, listings: pd.DataFrame, k: int = config.KNN_K,
                 alpha: float = config.RIDGE_ALPHA,
                 max_mean_distance: float = config.MAX_MEAN_DISTANCE):
        self.k = k
        self.max_mean_distance = max_mean_distance
        self.listings = listings.reset_index(drop=True).assign(
            city=lambda d: _city_key(d["cityname"], d["state"]))

        # Ridge: reference asking rent.
        x = self.listings[KNN_ATTRIBUTES + ["city", "state"]]
        self.reference_model = build_reference_model(alpha).fit(x, np.log(self.listings["price"]))

        # KNN: standardisation of the compared attributes and candidate groups.
        values = self.listings[KNN_ATTRIBUTES].to_numpy(dtype=float)
        self._mean, self._std = values.mean(axis=0), values.std(axis=0)
        self._std[self._std == 0] = 1.0  # constant attribute: compare raw differences
        self._z = (values - self._mean) / self._std
        self._by_city = self.listings.groupby("city").indices
        self._by_state = self.listings.groupby("state").indices

    # --- KNN -----------------------------------------------------------------
    def _candidates(self, listing: Listing) -> tuple[np.ndarray, EvidenceLevel]:
        empty = np.array([], dtype=int)
        city = self._by_city.get(_city_key(listing.cityname, listing.state), empty)
        if len(city) >= config.MIN_COMPARABLES:
            return city, "city"
        state = self._by_state.get(listing.state, empty)
        return state, ("state" if len(state) else "none")

    def comparables(self, listing: Listing) -> tuple[pd.DataFrame, EvidenceLevel, float | None]:
        """The k nearest listings, their evidence level and their mean distance."""
        candidates, level = self._candidates(listing)
        if len(candidates) == 0:
            return self.listings.iloc[[]], "none", None
        q = (np.array([getattr(listing, a) for a in KNN_ATTRIBUTES], dtype=float)
             - self._mean) / self._std
        dist = np.sqrt(((self._z[candidates] - q) ** 2).sum(axis=1))
        order = np.argsort(dist, kind="stable")[: self.k]
        rows = self.listings.iloc[candidates[order]].drop(columns="city")
        rows = rows.assign(distance=dist[order])
        return rows, level, float(dist[order].mean())

    # --- Ridge -----------------------------------------------------------------
    def reference_rent(self, listing: Listing) -> float:
        x = pd.DataFrame([{
            "square_feet": listing.square_feet, "bedrooms": listing.bedrooms,
            "bathrooms": listing.bathrooms,
            "city": _city_key(listing.cityname, listing.state), "state": listing.state,
        }])
        return float(np.exp(self.reference_model.predict(x)[0]))

    # --- A1 ------------------------------------------------------------------
    def assess(self, listing: Listing) -> PriceAssessment:
        comparables, level, mean_distance = self.comparables(listing)
        n = len(comparables)
        sufficient = (n >= self.k and mean_distance is not None
                      and mean_distance <= self.max_mean_distance)
        reference = self.reference_rent(listing)
        position = price_position(listing.price, reference) if sufficient else None
        scope = {"city": f"{listing.cityname}, {listing.state}",
                 "state": f"state {listing.state} (too few listings in {listing.cityname})",
                 "none": "no listings in the same city or state"}[level]
        return PriceAssessment(
            reference_rent=reference,
            position=position,
            n_comparables=n,
            evidence_sufficient=sufficient,
            comparables=comparables,
            method=f"Reference estimated by Ridge regression; comparable listings: "
                   f"the {n} most similar in {scope}.",
            level=level,
            mean_distance=mean_distance,
        )
