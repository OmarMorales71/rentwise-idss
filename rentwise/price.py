"""Price assessment: the interface to the data-driven model (Task 5).

The knowledge-based component only needs a `PriceAssessment`. Any object with
an `assess(listing) -> PriceAssessment` method can provide it (see the
`PriceAssessor` protocol). `ComparablesPriceAssessor` below is a simple
PLACEHOLDER so the system works end to end; Task 5's KNN / regression model
will replace it.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

import pandas as pd

from rentwise import config
from rentwise.preferences import Listing

Position = Literal["below", "in_line", "moderately_above", "significantly_above"]


@dataclass
class PriceAssessment:
    """Output of a price assessor.

    reference_rent: reference asking rent in 2019 USD per month (None if there
        are no comparables at all).
    position: price position of the asking rent; None when the evidence is
        insufficient, because then no price judgement is made.
    n_comparables: number of comparable listings behind the reference.
    evidence_sufficient: True when there is enough evidence for a judgement.
    comparables: the comparable listings used (rows of apartments_clean.csv).
    method: short description of how the reference was obtained (for the UI).
    """

    reference_rent: float | None
    position: Position | None
    n_comparables: int
    evidence_sufficient: bool
    comparables: pd.DataFrame = field(default_factory=pd.DataFrame)
    method: str = ""

    def gap(self, asking_rent: float) -> float | None:
        """Relative gap (asking - reference) / reference, e.g. 0.15 = 15% above."""
        if not self.reference_rent:
            return None
        return (asking_rent - self.reference_rent) / self.reference_rent


class PriceAssessor(Protocol):
    """What the knowledge-based component expects from the data-driven model."""

    def assess(self, listing: Listing) -> PriceAssessment: ...


def price_position(asking_rent: float, reference_rent: float) -> Position:
    """Place the asking rent relative to the reference (bands in config.py).

    Shared helper: Task 5's assessor should use it too, so that every assessor
    applies the same bands.
    """
    gap = (asking_rent - reference_rent) / reference_rent
    if gap < -config.IN_LINE_BAND:
        return "below"
    if gap <= config.IN_LINE_BAND:
        return "in_line"
    if gap <= config.MODERATE_BAND:
        return "moderately_above"
    return "significantly_above"


class ComparablesPriceAssessor:
    """PLACEHOLDER price assessor until Task 5's model is integrated.

    Comparables: same bedrooms, bathrooms within COMPARABLE_BATHROOMS_DIFF and
    floor area within COMPARABLE_SQUARE_FEET_DIFF, in the same city; widened to
    the same state when the city has fewer than MIN_COMPARABLES.
    Reference rent = median price of the comparables.
    """

    def __init__(self, listings: pd.DataFrame):
        self.listings = listings

    def _similar(self, listing: Listing) -> pd.DataFrame:
        df = self.listings
        return df[
            (df["bedrooms"] == listing.bedrooms)
            & ((df["bathrooms"] - listing.bathrooms).abs() <= config.COMPARABLE_BATHROOMS_DIFF)
            & ((df["square_feet"] - listing.square_feet).abs()
               <= config.COMPARABLE_SQUARE_FEET_DIFF * listing.square_feet)
        ]

    def assess(self, listing: Listing) -> PriceAssessment:
        similar = self._similar(listing)
        in_state = similar[similar["state"] == listing.state]
        comparables = in_state[in_state["cityname"] == listing.cityname]
        scope = f"{listing.cityname}, {listing.state}"
        if len(comparables) < config.MIN_COMPARABLES:
            comparables = in_state
            scope = f"state {listing.state} (too few in {listing.cityname})"

        n = len(comparables)
        sufficient = n >= config.MIN_COMPARABLES
        reference = float(comparables["price"].median()) if n > 0 else None
        position = price_position(listing.price, reference) if sufficient else None

        # Most similar floor area first, for display.
        comparables = comparables.assign(
            _size_diff=(comparables["square_feet"] - listing.square_feet).abs()
        ).sort_values("_size_diff").drop(columns="_size_diff")

        return PriceAssessment(
            reference_rent=reference,
            position=position,
            n_comparables=n,
            evidence_sufficient=sufficient,
            comparables=comparables,
            method=f"Median asking rent of similar listings in {scope} (placeholder for Task 5)",
        )
