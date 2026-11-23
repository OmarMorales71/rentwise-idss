"""RentWise Streamlit prototype.

Run from the repository root:  uv run streamlit run app/streamlit_app.py

This file only collects inputs and displays results. All decision logic lives
in the `rentwise` package and is reached through a single call to `assess()`.
"""

import sys
from pathlib import Path

# Make the `rentwise` package (in the repo root) importable when Streamlit runs this file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from rentwise import ComparablesPriceAssessor, Listing, Preference, assess  # noqa: E402
from rentwise.data import load_listings  # noqa: E402
from rentwise.preferences import (  # noqa: E402
    AMENITY_CRITERIA, NUMERIC_CRITERIA, PET_CRITERIA, criterion_label,
)

st.set_page_config(page_title="RentWise IDSS", layout="wide")

DATA_CAVEAT = ("Reference rents come from 2019 US asking rents (UCI Apartment for Rent "
               "Classified). They are not current market rents or agreed prices.")
PET_OPTIONS = ["Allowed", "Not allowed", "Not stated"]
OPTIONAL_CRITERIA = AMENITY_CRITERIA + PET_CRITERIA

# ---------------------------------------------------------------------------
# Example presets for the demo. Each one sets the listing and the preferences.
# ---------------------------------------------------------------------------
PRESETS = {
    "Shortlist: good fit, fair rent": dict(
        price=1200, sqft=950, bedrooms=2, bathrooms=2.0, state="TX", city="Houston",
        amen_listed=True, amenities=["amenity_parking", "amenity_pool", "amenity_gym"],
        cats="Allowed", dogs="Allowed",
        targets=dict(budget=1400, square_feet=900, bedrooms=2, bathrooms=1.5),
        weights=dict(budget=0.8, square_feet=0.5, bedrooms=1.0, bathrooms=0.3),
        extras={"amenity_parking": 0.6, "amenity_pool": 0.3},
    ),
    "Review: pet policy not stated": dict(
        price=1200, sqft=950, bedrooms=2, bathrooms=2.0, state="TX", city="Houston",
        amen_listed=True, amenities=["amenity_parking", "amenity_pool", "amenity_gym"],
        cats="Not stated", dogs="Not stated",
        targets=dict(budget=1400, square_feet=900, bedrooms=2, bathrooms=1.5),
        weights=dict(budget=0.8, square_feet=0.5, bedrooms=1.0, bathrooms=0.3),
        extras={"amenity_parking": 0.6, "dogs": 1.0},
    ),
    "Skip: over a non-negotiable budget": dict(
        price=2600, sqft=1000, bedrooms=2, bathrooms=2.0, state="CA", city="San Diego",
        amen_listed=True, amenities=["amenity_parking", "amenity_washer_dryer"],
        cats="Allowed", dogs="Allowed",
        targets=dict(budget=2200, square_feet=900, bedrooms=2, bathrooms=1.0),
        weights=dict(budget=1.0, square_feet=0.5, bedrooms=0.8, bathrooms=0.3),
        extras={"amenity_washer_dryer": 0.7},
    ),
}


@st.cache_data
def get_listings() -> pd.DataFrame:
    return load_listings()


@st.cache_resource
def get_price_assessor() -> ComparablesPriceAssessor:
    # Placeholder until Task 5's model is available: swap the assessor here.
    return ComparablesPriceAssessor(get_listings())


def apply_preset(name: str) -> None:
    """Write a preset into the widgets' session state."""
    p = PRESETS[name]
    ss = st.session_state
    for key in ("price", "sqft", "bedrooms", "bathrooms", "state", "city",
                "amen_listed", "amenities", "cats", "dogs"):
        ss[key] = p[key]
    for c in NUMERIC_CRITERIA:
        ss[f"target_{c}"] = p["targets"][c]
        ss[f"weight_{c}"] = min(p["weights"][c], 0.95)
        ss[f"nn_{c}"] = p["weights"][c] == 1.0
    ss["extras"] = list(p["extras"])
    for c in OPTIONAL_CRITERIA:
        w = p["extras"].get(c, 0.5)
        ss[f"weight_{c}"] = min(w, 0.95)
        ss[f"nn_{c}"] = w == 1.0


def on_preset_change() -> None:
    apply_preset(st.session_state["preset"])


def pet_value(choice: str) -> bool | None:
    return {"Allowed": True, "Not allowed": False, "Not stated": None}[choice]


def weight_input(criterion: str, container) -> float:
    """Weight slider plus a 'Non-negotiable' checkbox that forces the weight to 1.0."""
    left, right = container.columns([3, 2])
    nn = right.checkbox("Non-negotiable", key=f"nn_{criterion}")
    w = left.slider("Weight", 0.0, 1.0, step=0.05, key=f"weight_{criterion}", disabled=nn,
                    label_visibility="collapsed")
    return 1.0 if nn else w


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
try:
    listings = get_listings()
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

if "initialised" not in st.session_state:
    apply_preset(next(iter(PRESETS)))
    st.session_state["initialised"] = True

st.title("RentWise: apartment listing assessment")
st.caption(DATA_CAVEAT)

# ---------------------------------------------------------------------------
# Sidebar: the listing under assessment
# ---------------------------------------------------------------------------
with st.sidebar:
    st.selectbox("Example preset", list(PRESETS), key="preset", on_change=on_preset_change)
    st.header("The listing")
    st.number_input("Asking rent (USD / month)", min_value=100, max_value=20000, step=25,
                    key="price")
    st.number_input("Floor area (sq ft)", min_value=100, max_value=10000, step=10, key="sqft")
    st.number_input("Bedrooms", min_value=0, max_value=10, step=1, key="bedrooms")
    st.number_input("Bathrooms", min_value=0.0, max_value=10.0, step=0.5, key="bathrooms")

    states = sorted(listings["state"].unique())
    st.selectbox("State", states, key="state")
    cities = sorted(listings.loc[listings["state"] == st.session_state["state"], "cityname"].unique())
    if st.session_state.get("city") not in cities:
        st.session_state["city"] = cities[0]
    st.selectbox("City", cities, key="city")

    st.checkbox("The ad lists its amenities", key="amen_listed",
                help="Untick when the ad gives no amenity list: amenities are then unknown.")
    st.multiselect("Amenities in the ad", AMENITY_CRITERIA, format_func=criterion_label,
                   key="amenities", disabled=not st.session_state["amen_listed"])
    st.radio("Cats", PET_OPTIONS, key="cats", horizontal=True)
    st.radio("Dogs", PET_OPTIONS, key="dogs", horizontal=True)

listing = Listing(
    price=st.session_state["price"],
    square_feet=st.session_state["sqft"],
    bedrooms=st.session_state["bedrooms"],
    bathrooms=st.session_state["bathrooms"],
    cityname=st.session_state["city"],
    state=st.session_state["state"],
    amenities=set(st.session_state["amenities"]) if st.session_state["amen_listed"] else None,
    cats_allowed=pet_value(st.session_state["cats"]),
    dogs_allowed=pet_value(st.session_state["dogs"]),
)

# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------
with st.expander("Your preferences", expanded=True):
    st.caption("Give each criterion a target and a weight between 0 and 1 (0 = ignore). "
               "A non-negotiable criterion has weight 1.0: if the listing fails it, it is skipped.")
    preferences: list[Preference] = []
    target_labels = {"budget": "Budget (USD / month, at most)",
                     "square_feet": "Floor area (sq ft, at least)",
                     "bedrooms": "Bedrooms (at least)", "bathrooms": "Bathrooms (at least)"}
    steps = {"budget": 50, "square_feet": 25, "bedrooms": 1, "bathrooms": 0.5}
    cols = st.columns(len(NUMERIC_CRITERIA))
    for c, col in zip(NUMERIC_CRITERIA, cols):
        target = col.number_input(target_labels[c], min_value=0 * steps[c], step=steps[c],
                                  key=f"target_{c}")
        weight = weight_input(c, col)
        preferences.append(Preference(c, target, weight))

    extras = st.multiselect("Amenities and pet policy you care about", OPTIONAL_CRITERIA,
                            format_func=criterion_label, key="extras")
    extra_cols = st.columns(4)
    for i, c in enumerate(extras):
        box = extra_cols[i % 4].container(border=True)
        box.markdown(f"**{criterion_label(c)}**")
        preferences.append(Preference(c, weight=weight_input(c, box)))

# ---------------------------------------------------------------------------
# Assessment: the only call into the decision logic
# ---------------------------------------------------------------------------
result = assess(listing, preferences, get_price_assessor())

COLOURS = {"Shortlist": "#1e8449", "Review": "#b9770e", "Skip": "#b03a2e"}
st.markdown(
    f"<div style='background:{COLOURS[result.recommendation]};color:white;padding:18px;"
    f"border-radius:10px;text-align:center;font-size:42px;font-weight:700'>"
    f"{result.recommendation}</div>",
    unsafe_allow_html=True,
)

st.subheader("Why")
for reason in result.reasons:
    st.markdown(f"- {reason}")

fit_col, price_col = st.columns(2)

with fit_col:
    st.subheader("Personal fit")
    score = result.fit.score
    st.metric("Fit score (verifiable criteria)", "n/a" if score is None else f"{score:.2f}")
    rows = [{
        "criterion": criterion_label(r.criterion),
        "weight": r.weight,
        "non-negotiable": r.non_negotiable,
        "satisfaction": r.satisfaction,
        "contribution": round(r.contribution, 3),
    } for r in result.fit.breakdown]
    if rows:
        breakdown = pd.DataFrame(rows)
        st.bar_chart(breakdown.dropna(subset=["satisfaction"]).set_index("criterion")["satisfaction"],
                     horizontal=True, y_label="", x_label="satisfaction (0 to 1)")
        st.dataframe(breakdown, hide_index=True, width="stretch")
    if result.fit.unverifiable:
        st.warning("Not stated in the listing, left out of the score: "
                   + ", ".join(criterion_label(c) for c in result.fit.unverifiable))

with price_col:
    st.subheader("Price position")
    price = result.price
    a, b, c = st.columns(3)
    a.metric("Asking rent", f"${listing.price:,.0f}")
    gap = price.gap(listing.price)
    b.metric("Reference rent", "n/a" if price.reference_rent is None else f"${price.reference_rent:,.0f}",
             delta=None if gap is None else f"{gap:+.0%} vs reference", delta_color="inverse")
    c.metric("Comparables", price.n_comparables)
    if price.evidence_sufficient:
        st.markdown(f"Position: **{price.position.replace('_', ' ')}**")
    else:
        st.warning("Insufficient comparable evidence: no price judgement is made. "
                   "Any reference shown is indicative only.")
    st.caption(price.method)

st.subheader("Comparable listings used")
if price.n_comparables:
    show = ["title", "price", "square_feet", "bedrooms", "bathrooms", "cityname", "state", "listed_at"]
    st.dataframe(price.comparables[[c for c in show if c in price.comparables]].head(100),
                 hide_index=True, width="stretch")
    if price.n_comparables > 100:
        st.caption(f"Showing the 100 closest in floor area out of {price.n_comparables}.")
else:
    st.info("No comparable listings found in the dataset.")

st.info(DATA_CAVEAT)
