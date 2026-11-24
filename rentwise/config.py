"""System parameters of the knowledge-based component.

Every number that shapes a recommendation lives here, so that the values can be
found, discussed and tuned in one place. They are INITIAL VALUES chosen by the
team from common sense and the dataset summary in dataset/README.md. They have
not been validated yet: Task 7 (validation) is expected to tune them.
"""

# ---------------------------------------------------------------------------
# Satisfaction functions (personal fit)
# ---------------------------------------------------------------------------

# Budget: satisfaction is 1 when the rent is within the budget and falls
# linearly to 0 when the rent reaches budget * (1 + BUDGET_TOLERANCE).
# 0.20 means a rent 10% over budget is half satisfied, 20% over is not at all.
BUDGET_TOLERANCE = 0.20

# Floor area: satisfaction is 1 at or above the target and falls linearly to 0
# at target * (1 - SQUARE_FEET_TOLERANCE). Relative, because 100 sq ft matter
# more in a 500 sq ft studio than in a 1,500 sq ft flat.
SQUARE_FEET_TOLERANCE = 0.25

# Bedrooms: absolute band. With 2.0, one bedroom fewer than the target gives
# 0.5 and two fewer give 0.
BEDROOMS_BAND = 2.0

# Bathrooms: absolute band. With 1.0, half a bathroom fewer gives 0.5 and a
# full bathroom fewer gives 0.
BATHROOMS_BAND = 1.0

# A weight of exactly this value marks a preference as non-negotiable.
NON_NEGOTIABLE_WEIGHT = 1.0

# ---------------------------------------------------------------------------
# Price position (asking rent vs reference rent)
# ---------------------------------------------------------------------------

# gap = (asking rent - reference) / reference
#   gap <  -IN_LINE_BAND                     -> below
#   -IN_LINE_BAND <= gap <= IN_LINE_BAND     -> in_line
#   IN_LINE_BAND < gap <= MODERATE_BAND      -> moderately_above
#   gap > MODERATE_BAND                      -> significantly_above
IN_LINE_BAND = 0.10
MODERATE_BAND = 0.25

# ---------------------------------------------------------------------------
# Comparable listings (placeholder price assessor, until Task 5 is merged)
# ---------------------------------------------------------------------------

# Below this number of comparables the evidence is insufficient and no price
# judgement is made.
MIN_COMPARABLES = 10

# A historical listing is comparable when it has the same number of bedrooms,
# a number of bathrooms within this distance, and a floor area within this
# relative distance of the listing under assessment.
COMPARABLE_BATHROOMS_DIFF = 0.5
COMPARABLE_SQUARE_FEET_DIFF = 0.25

# ---------------------------------------------------------------------------
# Recommendation thresholds on the personal-fit score (0..1)
# ---------------------------------------------------------------------------

# fit < FIT_VERY_LOW                    -> very low fit (Skip, rule 2)
# FIT_VERY_LOW <= fit < FIT_GOOD        -> intermediate fit (Review, rule 3)
# fit >= FIT_GOOD                       -> good fit (can be Shortlisted)
FIT_VERY_LOW = 0.40
FIT_GOOD = 0.70
