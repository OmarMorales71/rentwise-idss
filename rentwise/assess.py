"""Single entry point of the IDSS: assess one listing for one renter."""

from dataclasses import dataclass

from rentwise.fit import FitResult, personal_fit
from rentwise.preferences import Listing, Preference
from rentwise.price import PriceAssessment, PriceAssessor
from rentwise.rules import Recommendation, recommend


@dataclass
class Assessment:
    recommendation: Recommendation   # "Shortlist", "Review" or "Skip"
    rule: str                        # rule that decided the class: "R1".."R4"
    reasons: list[str]
    fit: FitResult
    price: PriceAssessment


def assess(listing: Listing, preferences: list[Preference],
           price_assessor: PriceAssessor) -> Assessment:
    """Price assessment (A1) + personal fit (A2) -> recommendation (A3)."""
    price = price_assessor.assess(listing)
    fit = personal_fit(listing, preferences)
    rec, rule, reasons = recommend(fit, price, listing.price)
    return Assessment(rec, rule, reasons, fit, price)
