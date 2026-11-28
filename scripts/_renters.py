"""Simulated renters for the validation of the knowledge-based parameters.

There are no labelled recommendations (nobody knows the "right" class for a
listing), so the knowledge-based parameters are studied through the behaviour
of the system on a synthetic population of renters, one per assessed listing.
The population is not a claim about real renters: it is a fixed, documented,
seeded set of plausible situations, wide enough to exercise every criterion
and every rule. The assumptions are explained in report/validation_criteria.md.

Each renter is searching in the city of the listing they assess and states:

- budget: the local typical rent for the bedrooms they want x U(0.85, 1.25)
- bedrooms: the listing's bedrooms -1, +0 or +1 (probabilities 1/4, 1/2, 1/4)
- floor area: the local median floor area for those bedrooms x U(0.85, 1.15)
- bathrooms: 1, 1.5 or 2 (probabilities 1/2, 1/4, 1/4)
- weights of those four criteria: U(0.2, 0.9); budget is non-negotiable with
  probability 0.25 and bedrooms with probability 0.15
- each of five common amenities, with probability 0.3 and weight U(0.2, 0.8)
- dogs allowed as non-negotiable with probability 0.2; cats with probability 0.1

"Local" values come from the listings the system knows (the reference data),
by city and bedrooms, falling back to the state and then to the whole data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from rentwise.preferences import Listing, Preference

AMENITIES = ["amenity_parking", "amenity_washer_dryer", "amenity_gym", "amenity_pool",
             "amenity_dishwasher"]
SEED = 2019


class LocalMarket:
    """Typical rent and floor area by (city, bedrooms), then (state, bedrooms)."""

    def __init__(self, reference: pd.DataFrame):
        self.city = reference.groupby(["city", "bedrooms"])[["price", "square_feet"]].median()
        self.state = reference.groupby(["state", "bedrooms"])[["price", "square_feet"]].median()
        self.all = reference.groupby("bedrooms")[["price", "square_feet"]].median()

    def typical(self, city: str, state: str, bedrooms: int) -> tuple[float, float]:
        for table, key in ((self.city, (city, bedrooms)), (self.state, (state, bedrooms))):
            if key in table.index:
                row = table.loc[key]
                return float(row["price"]), float(row["square_feet"])
        nearest = self.all.index[np.abs(self.all.index - bedrooms).argmin()]
        row = self.all.loc[nearest]
        return float(row["price"]), float(row["square_feet"])


def simulate_renter(listing_row: pd.Series, market: LocalMarket,
                    rng: np.random.Generator) -> list[Preference]:
    bedrooms = max(0, int(listing_row["bedrooms"]) + int(rng.choice([-1, 0, 0, 1])))
    rent, area = market.typical(listing_row["city"], listing_row["state"], bedrooms)

    def weight(p_non_negotiable: float = 0.0) -> float:
        return 1.0 if rng.random() < p_non_negotiable else float(rng.uniform(0.2, 0.9))

    prefs = [
        Preference("budget", round(rent * rng.uniform(0.85, 1.25)), weight(0.25)),
        Preference("bedrooms", bedrooms, weight(0.15)),
        Preference("square_feet", round(area * rng.uniform(0.85, 1.15)), weight()),
        Preference("bathrooms", float(rng.choice([1.0, 1.0, 1.5, 2.0])), weight()),
    ]
    for amenity in AMENITIES:
        if rng.random() < 0.3:
            prefs.append(Preference(amenity, weight=float(rng.uniform(0.2, 0.8))))
    if rng.random() < 0.2:
        prefs.append(Preference("dogs", weight=1.0))
    if rng.random() < 0.1:
        prefs.append(Preference("cats", weight=1.0))
    return prefs


def simulate(listings: pd.DataFrame, reference: pd.DataFrame,
             seed: int = SEED) -> list[tuple[Listing, list[Preference]]]:
    """One (listing, preferences) pair per row of `listings`, reproducible."""
    market = LocalMarket(reference)
    rng = np.random.default_rng(seed)
    return [(Listing.from_row(row), simulate_renter(row, market, rng))
            for _, row in listings.iterrows()]
