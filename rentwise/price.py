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


def build_reference_model(alpha: float = config.RIDGE_ALPHA,
                          extra_columns: tuple[str, ...] = ()) -> Pipeline:
    """Ridge on log(price): standardised log floor area, bedrooms and bathrooms,
    and one-hot city and state. An unseen city gets all city indicators at zero,
    so its estimate rests on the state and the size of the apartment.

    extra_columns are passed through unchanged (e.g. amenity indicators); the
    system uses none, the model comparison uses them for one variant."""
    numeric = make_pipeline(
        FunctionTransformer(_log_floor_area, feature_names_out="one-to-one"),
        StandardScaler(),
    )
    parts = [
        ("numeric", numeric, KNN_ATTRIBUTES),
        ("location", OneHotEncoder(handle_unknown="ignore"), ["city", "state"]),
    ]
    if extra_columns:
        parts.append(("extra", "passthrough", list(extra_columns)))
    return Pipeline([("features", ColumnTransformer(parts)), ("ridge", Ridge(alpha=alpha))])


def _as_frame(listing: Listing) -> pd.DataFrame:
    return pd.DataFrame([{
        "price": listing.price, "square_feet": listing.square_feet,
        "bedrooms": listing.bedrooms, "bathrooms": listing.bathrooms,
        "cityname": listing.cityname, "state": listing.state,
    }])


@dataclass
class Neighbours:
    """KNN result for m query listings (rows padded with -1 / NaN when n < k)."""

    index: np.ndarray          # (m, k) row positions in the fitted listings
    distance: np.ndarray       # (m, k) standardised distances
    n: np.ndarray              # (m,) number of comparables found
    level: np.ndarray          # (m,) "city", "state" or "none"
    mean_distance: np.ndarray  # (m,) mean distance, NaN when n == 0


class RidgeKnnPriceAssessor:
    """Price assessment A1: Ridge reference + KNN comparables and evidence.

    Fitted once on the prepared listings. `assess` handles one listing (UI);
    `assess_frame` applies exactly the same steps to many listings at once
    (validation scripts).
    """

    def __init__(self, listings: pd.DataFrame, k: int = config.KNN_K,
                 alpha: float = config.RIDGE_ALPHA,
                 max_mean_distance: float | None = None):
        self.k = k
        self._max_mean_distance = max_mean_distance
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

    @property
    def max_mean_distance(self) -> float:
        """d_max; read from config at call time unless fixed in the constructor."""
        if self._max_mean_distance is not None:
            return self._max_mean_distance
        return config.MAX_MEAN_DISTANCE

    # --- KNN -----------------------------------------------------------------
    def _candidates(self, city: str, state: str) -> tuple[np.ndarray, str]:
        empty = np.array([], dtype=int)
        in_city = self._by_city.get(city, empty)
        if len(in_city) >= config.MIN_COMPARABLES:
            return in_city, "city"
        in_state = self._by_state.get(state, empty)
        return in_state, ("state" if len(in_state) else "none")

    def neighbours(self, frame: pd.DataFrame) -> Neighbours:
        """The k nearest listings for every row of `frame` (same city, or state)."""
        m, k = len(frame), self.k
        result = Neighbours(index=np.full((m, k), -1), distance=np.full((m, k), np.nan),
                            n=np.zeros(m, dtype=int), level=np.full(m, "none", dtype=object),
                            mean_distance=np.full(m, np.nan))
        z = (frame[KNN_ATTRIBUTES].to_numpy(dtype=float) - self._mean) / self._std
        cities = _city_key(frame["cityname"], frame["state"]).to_numpy()
        states = frame["state"].to_numpy()
        for (city, state), rows in pd.DataFrame({"c": cities, "s": states}).groupby(
                ["c", "s"]).indices.items():
            candidates, level = self._candidates(city, state)
            if len(candidates) == 0:
                continue
            dist = np.sqrt(((z[rows, None, :] - self._z[candidates][None, :, :]) ** 2).sum(axis=2))
            n = min(k, len(candidates))
            order = np.argsort(dist, axis=1, kind="stable")[:, :n]
            result.index[rows, :n] = candidates[order]
            result.distance[rows, :n] = np.take_along_axis(dist, order, axis=1)
            result.n[rows], result.level[rows] = n, level
            result.mean_distance[rows] = result.distance[rows, :n].mean(axis=1)
        return result

    def comparables(self, listing: Listing) -> tuple[pd.DataFrame, str, float | None]:
        """The k nearest listings, their evidence level and their mean distance."""
        nb = self.neighbours(_as_frame(listing))
        n = int(nb.n[0])
        rows = self.listings.iloc[nb.index[0, :n]].drop(columns="city")
        rows = rows.assign(distance=nb.distance[0, :n])
        mean = None if n == 0 else float(nb.mean_distance[0])
        return rows, str(nb.level[0]), mean

    # --- Ridge -----------------------------------------------------------------
    def reference_rents(self, frame: pd.DataFrame) -> np.ndarray:
        x = frame[KNN_ATTRIBUTES + ["state"]].assign(
            city=_city_key(frame["cityname"], frame["state"]))
        return np.exp(self.reference_model.predict(x))

    def reference_rent(self, listing: Listing) -> float:
        return float(self.reference_rents(_as_frame(listing))[0])

    # --- A1 ------------------------------------------------------------------
    def _sufficient(self, n: np.ndarray, mean_distance: np.ndarray) -> np.ndarray:
        with np.errstate(invalid="ignore"):
            return (n >= self.k) & (mean_distance <= self.max_mean_distance)

    def assess_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """A1 for many listings (columns as in apartments_clean.csv).

        Returns one row per listing: reference, gap, n_comparables, level,
        mean_distance, evidence_sufficient and position (None if insufficient).
        """
        nb = self.neighbours(frame)
        reference = self.reference_rents(frame)
        sufficient = self._sufficient(nb.n, nb.mean_distance)
        price = frame["price"].to_numpy(dtype=float)
        position = [price_position(p, r) if ok else None
                    for p, r, ok in zip(price, reference, sufficient)]
        return pd.DataFrame({
            "reference": reference, "gap": (price - reference) / reference,
            "n_comparables": nb.n, "level": nb.level, "mean_distance": nb.mean_distance,
            "evidence_sufficient": sufficient,
            "position": pd.Series(position, index=frame.index, dtype=object),
        }, index=frame.index)

    def assess(self, listing: Listing) -> PriceAssessment:
        comparables, level, mean_distance = self.comparables(listing)
        n = len(comparables)
        sufficient = bool(self._sufficient(np.array([n]),
                                           np.array([np.nan if mean_distance is None
                                                     else mean_distance]))[0])
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
