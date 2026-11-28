"""Personal-fit assessment: satisfaction functions, Weighted Sum Model and veto."""

from dataclasses import dataclass, field

from rentwise import config
from rentwise.preferences import Listing, Preference

# ---------------------------------------------------------------------------
# Satisfaction functions. Each returns a degree in [0, 1], or None when the
# listing does not state the information needed to check the criterion.
# ---------------------------------------------------------------------------


def budget_satisfaction(price: float, budget: float,
                        tolerance: float | None = None) -> float:
    """1 if price <= budget, then linear down to 0 at budget * (1 + tolerance)."""
    tolerance = config.BUDGET_TOLERANCE if tolerance is None else tolerance
    if price <= budget:
        return 1.0
    limit = budget * (1 + tolerance)
    if price >= limit:
        return 0.0
    return (limit - price) / (limit - budget)


def at_least_satisfaction(value: float, target: float, band: float) -> float:
    """1 if value >= target, then linear down to 0 at target - band."""
    if value >= target:
        return 1.0
    bottom = target - band
    if value <= bottom:
        return 0.0
    return (value - bottom) / band


def square_feet_satisfaction(square_feet: float, target: float,
                             tolerance: float | None = None) -> float:
    tolerance = config.SQUARE_FEET_TOLERANCE if tolerance is None else tolerance
    return at_least_satisfaction(square_feet, target, band=target * tolerance)


def bedrooms_satisfaction(bedrooms: float, target: float,
                          band: float | None = None) -> float:
    band = config.BEDROOMS_BAND if band is None else band
    return at_least_satisfaction(bedrooms, target, band)


def bathrooms_satisfaction(bathrooms: float, target: float,
                           band: float | None = None) -> float:
    band = config.BATHROOMS_BAND if band is None else band
    return at_least_satisfaction(bathrooms, target, band)


def yes_no_satisfaction(value: bool | None) -> float | None:
    """Amenities and pets: 1 if present / allowed, 0 if not, None if not stated."""
    if value is None:
        return None
    return 1.0 if value else 0.0


def satisfaction(listing: Listing, pref: Preference) -> float | None:
    """Degree to which `listing` satisfies one preference."""
    c = pref.criterion
    if c == "budget":
        return budget_satisfaction(listing.price, pref.target)
    if c == "square_feet":
        return square_feet_satisfaction(listing.square_feet, pref.target)
    if c == "bedrooms":
        return bedrooms_satisfaction(listing.bedrooms, pref.target)
    if c == "bathrooms":
        return bathrooms_satisfaction(listing.bathrooms, pref.target)
    if c == "cats":
        return yes_no_satisfaction(listing.cats_allowed)
    if c == "dogs":
        return yes_no_satisfaction(listing.dogs_allowed)
    # Amenity: unknown when the ad has no amenity list at all.
    if listing.amenities is None:
        return None
    return yes_no_satisfaction(c in listing.amenities)


# ---------------------------------------------------------------------------
# Weighted Sum Model
# ---------------------------------------------------------------------------


@dataclass
class CriterionResult:
    criterion: str
    weight: float
    non_negotiable: bool
    satisfaction: float | None       # None = cannot be verified from the listing
    normalised_weight: float = 0.0   # weight / sum of verifiable weights
    contribution: float = 0.0        # normalised_weight * satisfaction


@dataclass
class FitResult:
    score: float | None                      # None when no criterion is verifiable
    breakdown: list[CriterionResult] = field(default_factory=list)
    unverifiable: list[str] = field(default_factory=list)
    vetoes: list[str] = field(default_factory=list)  # non-negotiable, verifiable, not fully met

    @property
    def unverifiable_non_negotiable(self) -> list[str]:
        return [r.criterion for r in self.breakdown
                if r.non_negotiable and r.satisfaction is None]

    @property
    def limiting(self) -> list[CriterionResult]:
        """Verifiable criteria that are not fully satisfied, worst loss first."""
        partial = [r for r in self.breakdown
                   if r.satisfaction is not None and r.satisfaction < 1.0]
        return sorted(partial, key=lambda r: r.normalised_weight * (1 - r.satisfaction),
                      reverse=True)


def personal_fit(listing: Listing, preferences: list[Preference]) -> FitResult:
    """Score = sum(w_i * s_i) / sum(w_i) over the verifiable criteria only.

    Unverifiable criteria are left out of the score (weights renormalised) and
    reported. Preferences with weight 0 do not matter and are ignored.
    """
    results = [
        CriterionResult(p.criterion, p.weight, p.non_negotiable, satisfaction(listing, p))
        for p in preferences if p.weight > 0
    ]
    verifiable = [r for r in results if r.satisfaction is not None]
    total_weight = sum(r.weight for r in verifiable)

    score = None
    if total_weight > 0:
        for r in verifiable:
            r.normalised_weight = r.weight / total_weight
            r.contribution = r.normalised_weight * r.satisfaction
        score = sum(r.contribution for r in verifiable)

    return FitResult(
        score=score,
        breakdown=results,
        unverifiable=[r.criterion for r in results if r.satisfaction is None],
        vetoes=[r.criterion for r in verifiable if r.non_negotiable and r.satisfaction < 1.0],
    )
