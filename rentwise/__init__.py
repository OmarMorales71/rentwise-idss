"""RentWise knowledge-based component.

Typical use (UI, Task 9 integration):

    from rentwise import assess, Listing, Preference, RidgeKnnPriceAssessor
    result = assess(listing, preferences, RidgeKnnPriceAssessor(df))
"""

from rentwise.assess import Assessment, assess
from rentwise.fit import FitResult, personal_fit
from rentwise.preferences import Listing, Preference
from rentwise.price import PriceAssessment, PriceAssessor, RidgeKnnPriceAssessor

__all__ = [
    "Assessment", "assess", "FitResult", "personal_fit", "Listing", "Preference",
    "PriceAssessment", "PriceAssessor", "RidgeKnnPriceAssessor",
]
