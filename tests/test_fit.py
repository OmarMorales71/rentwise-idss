import pytest

from rentwise import config
from rentwise.fit import (
    bathrooms_satisfaction, bedrooms_satisfaction, budget_satisfaction, personal_fit,
    square_feet_satisfaction, yes_no_satisfaction,
)
from rentwise.preferences import Listing, Preference


def make_listing(**overrides) -> Listing:
    values = dict(price=1500, square_feet=900, bedrooms=2, bathrooms=1.0,
                  cityname="Austin", state="TX", amenities={"amenity_parking"},
                  cats_allowed=True, dogs_allowed=False)
    values.update(overrides)
    return Listing(**values)


# --- Satisfaction functions at their edges -----------------------------------

def test_budget_edges():
    tol = config.BUDGET_TOLERANCE
    assert budget_satisfaction(1000, 2000) == 1.0                 # well below
    assert budget_satisfaction(2000, 2000) == 1.0                 # exactly at budget
    assert budget_satisfaction(2000 * (1 + tol / 2), 2000) == pytest.approx(0.5)
    assert budget_satisfaction(2000 * (1 + tol), 2000) == 0.0     # end of band
    assert budget_satisfaction(5000, 2000) == 0.0                 # far above


def test_square_feet_edges():
    tol = config.SQUARE_FEET_TOLERANCE
    assert square_feet_satisfaction(1000, 800) == 1.0
    assert square_feet_satisfaction(800, 800) == 1.0
    assert square_feet_satisfaction(800 * (1 - tol / 2), 800) == pytest.approx(0.5)
    assert square_feet_satisfaction(800 * (1 - tol), 800) == 0.0
    assert square_feet_satisfaction(100, 800) == 0.0


def test_bedrooms_edges():
    band = config.BEDROOMS_BAND
    assert bedrooms_satisfaction(3, 2) == 1.0
    assert bedrooms_satisfaction(2, 2) == 1.0
    assert bedrooms_satisfaction(2 - band / 2, 2) == pytest.approx(0.5)
    assert bedrooms_satisfaction(2 - band, 2) == 0.0
    assert bedrooms_satisfaction(0, 0) == 1.0                     # studio wanted


def test_bathrooms_edges():
    band = config.BATHROOMS_BAND
    assert bathrooms_satisfaction(2, 1.5) == 1.0
    assert bathrooms_satisfaction(1.5, 1.5) == 1.0
    assert bathrooms_satisfaction(1.5 - band / 2, 1.5) == pytest.approx(0.5)
    assert bathrooms_satisfaction(1.5 - band, 1.5) == 0.0


def test_yes_no():
    assert yes_no_satisfaction(True) == 1.0
    assert yes_no_satisfaction(False) == 0.0
    assert yes_no_satisfaction(None) is None


def test_amenity_unknown_when_no_amenity_list():
    fit = personal_fit(make_listing(amenities=None), [Preference("amenity_pool", weight=0.5)])
    assert fit.unverifiable == ["amenity_pool"]
    assert fit.score is None


def test_amenity_listed_but_missing_is_zero():
    fit = personal_fit(make_listing(), [Preference("amenity_pool", weight=0.5)])
    assert fit.breakdown[0].satisfaction == 0.0


def test_pets_unknown_when_policy_not_stated():
    fit = personal_fit(make_listing(cats_allowed=None, dogs_allowed=None),
                       [Preference("dogs", weight=0.5)])
    assert fit.unverifiable == ["dogs"]


# --- Weighted Sum Model -------------------------------------------------------

def test_wsm_is_weighted_average():
    listing = make_listing(price=1500, amenities={"amenity_parking"})
    prefs = [Preference("budget", 2000, 0.6),             # satisfied: 1
             Preference("amenity_pool", weight=0.2)]      # missing: 0
    fit = personal_fit(listing, prefs)
    assert fit.score == pytest.approx(0.6 / 0.8)


def test_wsm_renormalises_over_verifiable_criteria():
    listing = make_listing(dogs_allowed=None)
    prefs = [Preference("budget", 2000, 0.5), Preference("dogs", weight=0.5)]
    fit = personal_fit(listing, prefs)
    assert fit.score == 1.0                 # only the budget counts
    assert fit.unverifiable == ["dogs"]


def test_zero_weight_is_ignored():
    fit = personal_fit(make_listing(), [Preference("budget", 2000, 0.5),
                                        Preference("amenity_pool", weight=0.0)])
    assert fit.score == 1.0
    assert [r.criterion for r in fit.breakdown] == ["budget"]


# --- Veto ---------------------------------------------------------------------

def test_veto_when_non_negotiable_not_fully_satisfied():
    listing = make_listing(price=2100)      # slightly over budget, satisfaction < 1
    fit = personal_fit(listing, [Preference("budget", 2000, 1.0)])
    assert 0 < fit.breakdown[0].satisfaction < 1
    assert fit.vetoes == ["budget"]


def test_no_veto_when_non_negotiable_satisfied():
    fit = personal_fit(make_listing(), [Preference("cats", weight=1.0)])
    assert fit.vetoes == []


def test_no_veto_when_non_negotiable_unverifiable():
    fit = personal_fit(make_listing(dogs_allowed=None), [Preference("dogs", weight=1.0)])
    assert fit.vetoes == []
    assert fit.unverifiable_non_negotiable == ["dogs"]


def test_preference_validation():
    with pytest.raises(ValueError):
        Preference("budget", 2000, 1.5)
    with pytest.raises(ValueError):
        Preference("balcony", weight=0.5)
    with pytest.raises(ValueError):
        Preference("budget", None, 0.5)
