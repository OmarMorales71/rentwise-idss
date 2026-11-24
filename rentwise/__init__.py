"""RentWise knowledge-based component.

Typical use (UI, Task 9 integration):

    from rentwise import assess, Listing, Preference, ComparablesPriceAssessor
    result = assess(listing, preferences, ComparablesPriceAssessor(df))
"""

from rentwise.assess import Assessment, assess
from rentwise.fit import FitResult, personal_fit
from rentwise.preferences import Listing, Preference
from rentwise.price import ComparablesPriceAssessor, PriceAssessment, PriceAssessor

__all__ = [
    "Assessment", "assess", "FitResult", "personal_fit", "Listing", "Preference",
    "ComparablesPriceAssessor", "PriceAssessment", "PriceAssessor",
]
