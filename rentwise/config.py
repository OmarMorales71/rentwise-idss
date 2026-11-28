"""System parameters of the IDSS.

Every number that shapes a recommendation lives here, so that the values can be
found, discussed and tuned in one place. All of them were checked or selected on
the validation period (September-November 2019): see results/calibration.md,
results/price_model_comparison.md and the criteria in report/validation_criteria.md.
"""

# ---------------------------------------------------------------------------
# Satisfaction functions (personal fit)
# ---------------------------------------------------------------------------
# Initial values set by the team, kept after the sensitivity analysis of
# scripts/calibrate_parameters.py (results/calibration.md, section 3).

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
# Calibrated on the validation period: IN_LINE_BAND = 50th percentile and
# MODERATE_BAND = 90th percentile of the absolute gap (results/calibration.md, section 2).
IN_LINE_BAND = 0.16
MODERATE_BAND = 0.49

# ---------------------------------------------------------------------------
# Price assessment models (report, Chapter 5)
# ---------------------------------------------------------------------------

# Ridge penalty, selected on the validation period (Sep-Nov 2019) by
# scripts/compare_price_models.py.
RIDGE_ALPHA = 1.0

# Number of comparable listings retrieved by KNN.
KNN_K = 10

# A city needs at least this many listings to supply the comparables; below it
# the search is widened to the state.
MIN_COMPARABLES = 10

# Evidence is sufficient when KNN finds KNN_K comparables AND their mean
# standardised distance (floor area, bedrooms, bathrooms) to the listing is at
# most this value. Calibrated on the validation period as the 95th percentile of
# the mean distance (results/calibration.md, section 1).
MAX_MEAN_DISTANCE = 1.69

# ---------------------------------------------------------------------------
# Recommendation thresholds on the personal-fit score (0..1)
# ---------------------------------------------------------------------------
# Initial values set by the team, kept after the sensitivity analysis
# (results/calibration.md, section 3).

# fit < FIT_VERY_LOW                    -> very low fit (Skip, rule 2)
# FIT_VERY_LOW <= fit < FIT_GOOD        -> intermediate fit (Review, rule 3)
# fit >= FIT_GOOD                       -> good fit (can be Shortlisted)
FIT_VERY_LOW = 0.40
FIT_GOOD = 0.70
