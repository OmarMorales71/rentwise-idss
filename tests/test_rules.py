import pandas as pd
import pytest

from rentwise import config
from rentwise.assess import assess
from rentwise.preferences import Listing, Preference
from rentwise.price import ComparablesPriceAssessor, PriceAssessment, price_position


class FixedPriceAssessor:
    """Stub assessor returning a given position, so each rule can be tested alone."""

    def __init__(self, position="in_line", sufficient=True, reference=1500.0, n=30):
        self.result = PriceAssessment(reference, position if sufficient else None, n, sufficient)

    def assess(self, listing):
        return self.result


def listing(**overrides) -> Listing:
    values = dict(price=1500, square_feet=900, bedrooms=2, bathrooms=1.0,
                  cityname="Austin", state="TX", amenities={"amenity_parking"},
                  cats_allowed=True, dogs_allowed=None)
    values.update(overrides)
    return Listing(**values)


GOOD_PREFS = [Preference("budget", 2000, 0.7), Preference("bedrooms", 2, 0.5)]


# --- Each rule branch ---------------------------------------------------------

def test_r4_shortlist():
    result = assess(listing(), GOOD_PREFS, FixedPriceAssessor("in_line"))
    assert (result.recommendation, result.rule) == ("Shortlist", "R4")


def test_r4_shortlist_when_below_reference():
    result = assess(listing(), GOOD_PREFS, FixedPriceAssessor("below"))
    assert result.recommendation == "Shortlist"


def test_r1_veto_skips_even_with_good_price_and_fit():
    prefs = GOOD_PREFS + [Preference("amenity_pool", weight=1.0)]
    result = assess(listing(), prefs, FixedPriceAssessor("below"))
    assert (result.recommendation, result.rule) == ("Skip", "R1")
    assert "pool" in result.reasons[0]


def test_r1_takes_precedence_over_r3():
    prefs = [Preference("budget", 1000, 1.0), Preference("dogs", weight=1.0)]
    result = assess(listing(), prefs, FixedPriceAssessor(sufficient=False, n=2))
    assert result.rule == "R1"


def test_r2_significantly_above_with_sufficient_evidence():
    result = assess(listing(), GOOD_PREFS, FixedPriceAssessor("significantly_above"))
    assert (result.recommendation, result.rule) == ("Skip", "R2")


def test_r2_very_low_fit():
    prefs = [Preference("budget", 1000, 0.9), Preference("bedrooms", 4, 0.9)]
    result = assess(listing(), prefs, FixedPriceAssessor("in_line"))
    assert result.fit.score < config.FIT_VERY_LOW
    assert (result.recommendation, result.rule) == ("Skip", "R2")


def test_r3_unverifiable_non_negotiable_is_review_not_skip():
    prefs = GOOD_PREFS + [Preference("dogs", weight=1.0)]
    result = assess(listing(dogs_allowed=None), prefs, FixedPriceAssessor("in_line"))
    assert (result.recommendation, result.rule) == ("Review", "R3")
    assert any("dogs allowed" in r for r in result.reasons)


def test_r3_insufficient_evidence():
    result = assess(listing(), GOOD_PREFS, FixedPriceAssessor(sufficient=False, n=3))
    assert (result.recommendation, result.rule) == ("Review", "R3")


def test_insufficient_evidence_never_gives_price_based_skip():
    # Asking rent far above the reference of a handful of comparables.
    assessor = FixedPriceAssessor(sufficient=False, reference=800.0, n=3)
    result = assess(listing(price=3000), [Preference("budget", 4000, 0.5)], assessor)
    assert result.recommendation == "Review"


def test_r3_moderately_above():
    result = assess(listing(), GOOD_PREFS, FixedPriceAssessor("moderately_above"))
    assert (result.recommendation, result.rule) == ("Review", "R3")


def test_r3_intermediate_fit():
    prefs = [Preference("budget", 2000, 0.5), Preference("amenity_pool", weight=0.5)]
    result = assess(listing(), prefs, FixedPriceAssessor("in_line"))
    assert config.FIT_VERY_LOW <= result.fit.score < config.FIT_GOOD
    assert (result.recommendation, result.rule) == ("Review", "R3")


def test_r3_no_verifiable_criterion():
    result = assess(listing(amenities=None), [Preference("amenity_pool", weight=0.5)],
                    FixedPriceAssessor("in_line"))
    assert result.fit.score is None
    assert result.recommendation == "Review"


def test_reasons_report_gap_and_comparables():
    result = assess(listing(price=1650), GOOD_PREFS,
                    FixedPriceAssessor("in_line", reference=1500.0, n=42))
    price_reason = [r for r in result.reasons if r.startswith("Price")][0]
    assert "10% above" in price_reason and "42 comparable" in price_reason


# --- Price position and placeholder assessor ----------------------------------

@pytest.mark.parametrize("asking, expected", [
    (850, "below"), (900, "in_line"), (1100, "in_line"),
    (1200, "moderately_above"), (1250, "moderately_above"), (1300, "significantly_above"),
])
def test_price_position_bands(asking, expected):
    assert price_position(asking, 1000) == expected


def _history(n_city: int, n_state_other: int) -> pd.DataFrame:
    rows = [dict(price=1000 + i, square_feet=900, bedrooms=2, bathrooms=1.0,
                 cityname="Austin", state="TX") for i in range(n_city)]
    rows += [dict(price=2000, square_feet=900, bedrooms=2, bathrooms=1.0,
                  cityname="Dallas", state="TX") for _ in range(n_state_other)]
    rows += [dict(price=9000, square_feet=900, bedrooms=2, bathrooms=1.0,
                  cityname="Austin", state="MN")]       # same city name, other state
    return pd.DataFrame(rows)


def test_comparables_same_city_when_enough():
    result = ComparablesPriceAssessor(_history(config.MIN_COMPARABLES, 5)).assess(listing())
    assert result.n_comparables == config.MIN_COMPARABLES
    assert set(result.comparables["cityname"]) == {"Austin"}
    assert set(result.comparables["state"]) == {"TX"}
    assert result.evidence_sufficient


def test_comparables_widen_to_state():
    result = ComparablesPriceAssessor(_history(2, config.MIN_COMPARABLES)).assess(listing())
    assert result.n_comparables == 2 + config.MIN_COMPARABLES
    assert result.evidence_sufficient


def test_comparables_insufficient_evidence_has_no_position():
    result = ComparablesPriceAssessor(_history(2, 3)).assess(listing())
    assert not result.evidence_sufficient
    assert result.position is None
    assert result.n_comparables == 5


def test_comparables_exclude_dissimilar_listings():
    history = _history(config.MIN_COMPARABLES, 0)
    history.loc[0, "bedrooms"] = 3
    history.loc[1, "square_feet"] = 2000
    result = ComparablesPriceAssessor(history).assess(listing())
    assert result.n_comparables == config.MIN_COMPARABLES - 2
