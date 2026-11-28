"""Recommendation rules: combine personal fit and price position.

The rules are applied in a fixed order of precedence (report, chapter "Main
Identified Decisions", section Recommendation). The first rule that fires
decides the class:

  R1  A non-negotiable criterion is verifiable and not fully satisfied -> Skip
  R2  Significantly above the reference WITH sufficient evidence,
      or a very low personal fit                                     -> Skip
  R3  An unverifiable non-negotiable criterion, insufficient evidence,
      moderately above the reference, or an intermediate (or unknown)
      personal fit                                                   -> Review
  R4  Otherwise                                                      -> Shortlist
"""

from typing import Literal

from rentwise import config
from rentwise.fit import FitResult
from rentwise.preferences import criterion_label
from rentwise.price import PriceAssessment

Recommendation = Literal["Shortlist", "Review", "Skip"]

POSITION_TEXT = {
    "below": "below the reference",
    "in_line": "in line with the reference",
    "moderately_above": "moderately above the reference",
    "significantly_above": "significantly above the reference",
}


def _names(criteria: list[str]) -> str:
    return ", ".join(criterion_label(c) for c in criteria)


def _evidence_problem(price: PriceAssessment) -> str:
    """Why the comparable evidence is insufficient: too few or too dissimilar."""
    if price.n_comparables < config.KNN_K:
        return f"{price.n_comparables} comparables, at least {config.KNN_K} needed"
    if price.mean_distance is not None:
        return (f"comparables too dissimilar: mean distance {price.mean_distance:.2f}, "
                f"at most {config.MAX_MEAN_DISTANCE:.2f} allowed")
    return "comparables too dissimilar"


def recommend(fit: FitResult, price: PriceAssessment,
              asking_rent: float) -> tuple[Recommendation, str, list[str]]:
    """Return (recommendation, rule id, human-readable reasons)."""
    score = fit.score
    very_low_fit = score is not None and score < config.FIT_VERY_LOW
    good_fit = score is not None and score >= config.FIT_GOOD
    overpriced = price.evidence_sufficient and price.position == "significantly_above"
    moderately_above = price.evidence_sufficient and price.position == "moderately_above"

    reasons: list[str] = []

    # --- Rule that fired --------------------------------------------------
    if fit.vetoes:
        rec, rule = "Skip", "R1"
        reasons.append(f"R1: non-negotiable criterion not satisfied: {_names(fit.vetoes)}.")
    elif overpriced or very_low_fit:
        rec, rule = "Skip", "R2"
        if overpriced:
            reasons.append("R2: the asking rent is significantly above the reference, "
                           "based on sufficient comparable listings.")
        if very_low_fit:
            reasons.append(f"R2: very low personal fit ({score:.2f} < {config.FIT_VERY_LOW:.2f}).")
    elif (fit.unverifiable_non_negotiable or not price.evidence_sufficient
          or moderately_above or not good_fit):
        rec, rule = "Review", "R3"
        if fit.unverifiable_non_negotiable:
            reasons.append("R3: a non-negotiable criterion cannot be verified from the "
                           f"listing: {_names(fit.unverifiable_non_negotiable)}.")
        if not price.evidence_sufficient:
            reasons.append(f"R3: insufficient comparable evidence ({_evidence_problem(price)}); "
                           "no price judgement is made.")
        if moderately_above:
            reasons.append("R3: the asking rent is moderately above the reference.")
        if score is None:
            reasons.append("R3: none of the weighted criteria can be verified, so the "
                           "personal fit is unknown.")
        elif not good_fit:
            reasons.append(f"R3: intermediate personal fit ({score:.2f}, "
                           f"{config.FIT_GOOD:.2f} needed for Shortlist).")
    else:
        rec, rule = "Shortlist", "R4"
        reasons.append("R4: no non-negotiable criterion fails, the personal fit is good "
                       "and the asking rent is reasonable relative to comparable listings.")

    # --- Supporting evidence, always reported -----------------------------
    if score is not None:
        reasons.append(f"Personal fit: {score:.2f} over the verifiable criteria.")
    limiting = fit.limiting
    if limiting:
        details = ", ".join(f"{criterion_label(r.criterion)} ({r.satisfaction:.2f})"
                            for r in limiting)
        reasons.append(f"Criteria that limited the score: {details}.")
    if fit.unverifiable:
        reasons.append("Not stated in the listing (ask the advertiser): "
                       f"{_names(fit.unverifiable)}.")

    gap = price.gap(asking_rent)
    if gap is not None:
        rel = f"{abs(gap):.0%} {'above' if gap >= 0 else 'below'}"
        reference = f"${price.reference_rent:,.0f}"
        if price.evidence_sufficient:
            reasons.append(f"Price: asking ${asking_rent:,.0f} is {rel} the reference {reference} "
                           f"({POSITION_TEXT[price.position]}), "
                           f"from {price.n_comparables} comparable listings.")
        else:
            reasons.append(f"Price (indicative only, not used in the decision): asking "
                           f"${asking_rent:,.0f} is {rel} the reference {reference}, "
                           f"but the comparable evidence is insufficient.")
    else:
        reasons.append("Price: no comparable listings found.")

    return rec, rule, reasons
