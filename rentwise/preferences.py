"""Data structures: the listing under assessment and the renter's preferences."""

from dataclasses import dataclass

import pandas as pd

from rentwise import config

# Amenity criteria use exactly the names of the amenity_* columns of
# dataset/processed/apartments_clean.csv.
AMENITY_CRITERIA = [
    "amenity_ac", "amenity_alarm", "amenity_basketball", "amenity_cable_or_satellite",
    "amenity_clubhouse", "amenity_dishwasher", "amenity_doorman", "amenity_elevator",
    "amenity_fireplace", "amenity_garbage_disposal", "amenity_gated", "amenity_golf",
    "amenity_gym", "amenity_hot_tub", "amenity_internet_access", "amenity_luxury",
    "amenity_parking", "amenity_patio_deck", "amenity_playground", "amenity_pool",
    "amenity_refrigerator", "amenity_storage", "amenity_tennis", "amenity_tv",
    "amenity_view", "amenity_washer_dryer", "amenity_wood_floors",
]

# Criteria with a numeric target and a gradual (0..1) satisfaction.
NUMERIC_CRITERIA = ["budget", "square_feet", "bedrooms", "bathrooms"]

# Pet criteria: "the listing must allow cats / dogs".
PET_CRITERIA = ["cats", "dogs"]

ALL_CRITERIA = NUMERIC_CRITERIA + AMENITY_CRITERIA + PET_CRITERIA


def criterion_label(criterion: str) -> str:
    """Human-readable name, e.g. 'amenity_washer_dryer' -> 'washer dryer'."""
    labels = {"budget": "budget", "square_feet": "floor area", "cats": "cats allowed",
              "dogs": "dogs allowed"}
    if criterion in labels:
        return labels[criterion]
    return criterion.removeprefix("amenity_").replace("_", " ")


@dataclass
class Listing:
    """The apartment listing the renter wants to assess.

    amenities: the set of amenity criteria the ad lists (e.g. {"amenity_pool"}),
        or None when the ad gives no amenity list at all.
    cats_allowed / dogs_allowed: True / False, or None when the ad does not
        state a pet policy.
    """

    price: float
    square_feet: float
    bedrooms: int
    bathrooms: float
    cityname: str
    state: str
    amenities: set[str] | None = None
    cats_allowed: bool | None = None
    dogs_allowed: bool | None = None

    @classmethod
    def from_row(cls, row: pd.Series) -> "Listing":
        """Build a Listing from a row of apartments_clean.csv."""
        if bool(row["amenities_listed"]):
            amenities = {c for c in AMENITY_CRITERIA if c in row and row[c] == 1}
        else:
            amenities = None

        def pet(value) -> bool | None:
            return None if pd.isna(value) else bool(value)

        return cls(
            price=float(row["price"]),
            square_feet=float(row["square_feet"]),
            bedrooms=int(row["bedrooms"]),
            bathrooms=float(row["bathrooms"]),
            cityname=str(row["cityname"]),
            state=str(row["state"]),
            amenities=amenities,
            cats_allowed=pet(row["cats_allowed"]),
            dogs_allowed=pet(row["dogs_allowed"]),
        )


@dataclass
class Preference:
    """One criterion the renter cares about.

    target: the budget in USD, the minimum floor area / bedrooms / bathrooms.
        Ignored for amenities and pets ("the listing must have / allow it").
    weight: importance in [0, 1]; 1.0 means non-negotiable.
    """

    criterion: str
    target: float | None = None
    weight: float = 0.5

    def __post_init__(self) -> None:
        if self.criterion not in ALL_CRITERIA:
            raise ValueError(f"Unknown criterion: {self.criterion!r}")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be in [0, 1], got {self.weight}")
        if self.criterion in NUMERIC_CRITERIA and self.target is None:
            raise ValueError(f"Criterion {self.criterion!r} needs a target value")

    @property
    def non_negotiable(self) -> bool:
        return self.weight >= config.NON_NEGOTIABLE_WEIGHT
