"""
U.S. News College Ranking Dashboard
-----------------------------------
Ordinal rank history for every ranked National University and National Liberal Arts
College across every edition U.S. News has published (1984-2026). Any institution can
be selected as the profile focus.

Run:  streamlit run app.py

Sources are listed in SOURCES.md and reproduced in the sidebar. This app deliberately
contains nothing but U.S. News ranking data: no IPEDS, Common Data Set, or internal
institutional-research figures.
"""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------- config

st.set_page_config(
    page_title="U.S. News College Ranking Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit's default metric type scale is built for two or three big numbers. This row
# carries four, including school names, so the value size is dialled back to fit.
st.markdown(
    """
    <style>
      [data-testid="stMetricValue"] {
          font-size: 1.35rem;
          font-weight: 600;
          line-height: 1.25;
          overflow-wrap: anywhere;
      }
      [data-testid="stMetricLabel"] p {
          font-size: 0.78rem;
          letter-spacing: .02em;
          opacity: .75;
      }
      [data-testid="stMetricDelta"] {
          font-size: 0.82rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_FOCUS = "Harvard University"   # opens here; any institution can be selected
LATEST_PUBLIC = 2026          # newest publicly released edition
NEXT_EDITION = 2027           # publishes September 2026
CAT_LABEL = {"lac": "National Liberal Arts Colleges", "nu": "National Universities"}

DATA_PATH = Path(__file__).parent / "data" / "rankings.json"

SOURCES = [
    ("Andrew G. Reiter, U.S. News Historical Rankings datasets "
     "(liberal arts .xlsx, national universities .xlsx)",
     "https://www.andyreiter.com/datasets/"),
    ("U.S. News — The 2026 Best Colleges Rankings Are Out",
     "https://www.usnews.com/education/best-colleges/articles/us-news-ranks-best-colleges"),
    ("U.S. News — Updates to the 2027 College Data Collection (confirms 2027 timing)",
     "https://www.usnews.com/education/blogs/college-rankings-blog/articles/"
     "2026-05-13/beyond-first-time-full-time-students-updates-to-the-2027-college-data-collection"),
    ("U.S. News — 2026 Best National Liberal Arts Colleges",
     "https://www.usnews.com/best-colleges/rankings/national-liberal-arts-colleges"),
]


# ----------------------------------------------------------------------------- data

@st.cache_data(show_spinner=False)
def load_data(path: Path):
    """Return (long dataframe, per-school summary, list of editions)."""
    payload = json.loads(path.read_text(encoding="utf-8"))

    rows = []
    for school in payload["schools"]:
        for year, value in school["h"].items():
            rows.append(
                {
                    "school": school["n"],
                    "state": school["s"],
                    "ipeds": school["i"],
                    "category": CAT_LABEL[school["t"]],
                    "cat_key": school["t"],
                    # IPEDS CONTROL, joined on unit id. "Unknown" is almost always a
                    # closed institution that has aged out of the IPEDS directory.
                    "control": school.get("c", "Unknown"),
                    "edition": int(year),
                    # Liberal arts editions before 2004 used tiers/quartiles rather than
                    # ordinal positions. Those arrive as strings and must never be
                    # sorted, averaged or charted as if they were ranks.
                    "rank": value if isinstance(value, int) else None,
                    "tier": None if isinstance(value, int) else str(value),
                }
            )

    long = pd.DataFrame(rows).sort_values(["school", "edition"])
    long["prev"] = long.groupby("school")["rank"].shift(1)
    long["prev_edition"] = long.groupby("school")["edition"].shift(1)
    # Only call it a one-year move when the previous row really is the previous edition.
    consecutive = long["prev_edition"] == long["edition"] - 1
    long["change"] = (long["prev"] - long["rank"]).where(consecutive)

    ranked = long.dropna(subset=["rank"])
    summary = ranked.groupby(
        ["school", "state", "category", "cat_key", "control"], as_index=False
    ).agg(
        best=("rank", "min"),
        worst=("rank", "max"),
        editions=("rank", "count"),
        first_edition=("edition", "min"),
        last_edition=("edition", "max"),
    )
    summary["swing"] = summary["worst"] - summary["best"]
    best_year = (
        ranked.loc[ranked.groupby("school")["rank"].idxmin(), ["school", "edition"]]
        .rename(columns={"edition": "best_edition"})
    )
    summary = summary.merge(best_year, on="school", how="left")

    return long, summary, sorted(long["edition"].unique(), reverse=True)


LONG, SUMMARY, EDITIONS = load_data(DATA_PATH)


def series_for(school: str) -> pd.DataFrame:
    """Published ordinal rank series for one school."""
    return (
        LONG[(LONG["school"] == school) & LONG["rank"].notna()][["edition", "rank"]]
        .sort_values("edition")
        .reset_index(drop=True)
    )


def rank_chart(df: pd.DataFrame, color_field: str | None = None, height: int = 340):
    """Line chart on a reversed axis, because rank 1 belongs at the top."""
    lo, hi = df["rank"].min(), df["rank"].max()
    pad = max(3, (hi - lo) * 0.12)
    scale = alt.Scale(domain=[max(1, lo - pad), hi + pad], reverse=True)

    enc = {
        "x": alt.X("edition:O", title="Edition", axis=alt.Axis(labelAngle=0)),
        "y": alt.Y("rank:Q", title="Rank (lower is better)", scale=scale),
        "tooltip": [alt.Tooltip("edition:O", title="Edition"),
                    alt.Tooltip("rank:Q", title="Rank")],
    }
    if color_field:
        enc["color"] = alt.Color(f"{color_field}:N", title=None)
        enc["tooltip"].insert(0, alt.Tooltip(f"{color_field}:N", title=""))

    base = alt.Chart(df).encode(**enc)
    return (base.mark_line(strokeWidth=2)
            + base.mark_point(size=45, filled=True)).properties(height=height)


def fmt_move(value) -> str:
    """Signed string for st.metric's delta, which draws its own arrow and colour."""
    return "—" if pd.isna(value) else f"{int(value):+d}"


# -------------------------------------------------------------------------- sidebar

st.sidebar.title("🎓 U.S. News Rankings")
st.sidebar.caption(
    f"{SUMMARY['school'].nunique():,} institutions · editions "
    f"{min(EDITIONS)}–{max(EDITIONS)}"
)

edition = st.sidebar.selectbox(
    "Edition", EDITIONS,
    index=EDITIONS.index(LATEST_PUBLIC),
    format_func=lambda y: f"{y} (latest public)" if y == LATEST_PUBLIC else str(y),
)
category = st.sidebar.radio("Category", ["All"] + list(CAT_LABEL.values()), index=0)
states = sorted(s for s in SUMMARY["state"].dropna().unique())
state_pick = st.sidebar.selectbox("State", ["All states"] + states, index=0)
CONTROL_ORDER = ["Public", "Private not-for-profit", "Private for-profit", "Unknown"]
controls_present = [c for c in CONTROL_ORDER if c in set(LONG["control"])]
control_pick = st.sidebar.selectbox("Control", ["All sectors"] + controls_present, index=0)

query = st.sidebar.text_input("Search school", placeholder="e.g. Harvard")

st.sidebar.divider()
# LONG, not SUMMARY: SUMMARY holds only schools with at least one ordinal rank,
# which would hide tier-only schools such as Adrian and Olivet.
ALL_SCHOOLS = sorted(LONG["school"].unique())

# The search box narrows this list too, so typing a few letters is a faster way to reach
# a school than scrolling 567 options.
term = query.strip().lower()
focus_options = [s for s in ALL_SCHOOLS if term in s.lower()] if term else ALL_SCHOOLS
narrowed = bool(term) and len(focus_options) < len(ALL_SCHOOLS)
if term and not focus_options:
    st.sidebar.caption(
        f":orange[No school matches “{query.strip()}”.] Showing all institutions."
    )
    focus_options = ALL_SCHOOLS
    narrowed = False

focus = st.sidebar.selectbox(
    "Focus institution",
    focus_options,
    index=focus_options.index(DEFAULT_FOCUS) if DEFAULT_FOCUS in focus_options else 0,
    help="Drives the profile tab and the peer group. The search box above narrows this "
         "list.",
)
if narrowed:
    st.sidebar.caption(
        f"{len(focus_options)} of {len(ALL_SCHOOLS)} institutions match “{query.strip()}”."
    )

st.sidebar.divider()
st.sidebar.warning(
    f"**Latest published edition is {LATEST_PUBLIC}.** The {NEXT_EDITION} edition "
    "releases September 2026, so no school in this dataset has a "
    f"{NEXT_EDITION} rank yet."
)
st.sidebar.info(
    "**Not covered:** Regional Universities and Regional Colleges. No multi-year public "
    "dataset exists for those categories, so many small private colleges that rank there "
    "do not appear here at all."
)
st.sidebar.divider()
st.sidebar.markdown("**Sources**")
for label, url in SOURCES:
    st.sidebar.markdown(f"- [{label}]({url})")

# ----------------------------------------------------------------------------- main

st.title("U.S. News College Ranking Dashboard")

tab_explore, tab_compare, tab_home = st.tabs(
    ["Explorer", "Compare schools", "Institution profile 📍"]
)

# --- Explorer -----------------------------------------------------------------

with tab_explore:
    view = LONG[(LONG["edition"] == edition) & LONG["rank"].notna()].copy()
    if category != "All":
        view = view[view["category"] == category]
    if state_pick != "All states":
        view = view[view["state"] == state_pick]
    if control_pick != "All sectors":
        view = view[view["control"] == control_pick]
    if query.strip():
        view = view[view["school"].str.contains(query.strip(), case=False, na=False)]
    view = view.merge(
        SUMMARY[["school", "best", "worst", "best_edition"]], on="school", how="left"
    ).sort_values("rank")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Schools listed", f"{len(view):,}")
    movers = view.dropna(subset=["change"])
    if not movers.empty:
        up = movers.loc[movers["change"].idxmax()]
        down = movers.loc[movers["change"].idxmin()]
        c2.metric("Biggest riser", up["school"][:22], fmt_move(up["change"]))
        c3.metric("Biggest faller", down["school"][:22], fmt_move(down["change"]))
        med = view["change"].median()
        c4.metric("Median 1-yr move", "—" if pd.isna(med) else f"{med:+.0f}",
                  help="Positive means the typical school in this filter moved up.")

    st.dataframe(
        view[["school", "state", "control", "category", "rank", "change",
              "best", "worst", "best_edition"]],
        width="stretch", hide_index=True, height=520,
        column_config={
            "school": st.column_config.TextColumn("School", width="large"),
            "state": st.column_config.TextColumn("St", width="small"),
            "control": st.column_config.TextColumn("Sector", width="medium"),
            "category": st.column_config.TextColumn("Category", width="medium"),
            "rank": st.column_config.NumberColumn(f"{edition} rank", format="%d"),
            "change": st.column_config.NumberColumn("1-yr", format="%+d",
                                                    help="Positive = moved up"),
            "best": st.column_config.NumberColumn("Best ever", format="%d"),
            "worst": st.column_config.NumberColumn("Worst ever", format="%d"),
            "best_edition": st.column_config.NumberColumn("Best in", format="%d"),
        },
    )

    st.download_button(
        "Download this view (CSV)",
        view.drop(columns=["cat_key", "prev", "prev_edition", "tier"], errors="ignore")
            .to_csv(index=False).encode("utf-8"),
        file_name=f"usnews_{edition}_{category.replace(' ', '_').lower()}.csv",
        mime="text/csv",
    )

    if not view.empty:
        mix = view["control"].value_counts()
        share = ", ".join(
            f"{n} {label.lower()} ({n / len(view):.0%})" for label, n in mix.items()
        )
        st.caption(f"Sector mix of this view: {share}.")

    tiers = LONG[(LONG["edition"] == edition) & LONG["tier"].notna()]
    if not tiers.empty:
        with st.expander(
            f"{len(tiers)} schools placed in tiers rather than ranked in {edition}"
        ):
            st.caption(
                "U.S. News grouped liberal arts colleges into tiers and quartiles before "
                "the 2004 edition. These are bands, not positions, and are excluded from "
                "every calculation above."
            )
            st.dataframe(tiers[["school", "state", "tier"]].sort_values("school"),
                         width="stretch", hide_index=True)

# --- Compare ------------------------------------------------------------------

with tab_compare:
    st.subheader("Overlay rank histories")

    focus_row = LONG[LONG["school"] == focus].iloc[0]
    peer_group = sorted(
        SUMMARY[(SUMMARY["state"] == focus_row["state"])
                & (SUMMARY["cat_key"] == focus_row["cat_key"])]["school"]
    )
    preset = st.radio(
        "Start from",
        ["Peer group", "Pick my own"],
        horizontal=True,
        help=f"Peer group = {focus_row['state']} schools in the same category as {focus}.",
    )
    default = peer_group if preset == "Peer group" else [focus]

    MAX_COMPARE = 12
    if len(default) > MAX_COMPARE:
        st.caption(
            f"{focus_row['state']} has {len(default)} ranked schools in this category — "
            f"showing the first {MAX_COMPARE}. Add or swap any below."
        )
        default = default[:MAX_COMPARE]
    picks = st.multiselect("Schools", ALL_SCHOOLS, default=default,
                           max_selections=MAX_COMPARE)

    if picks:
        frames = []
        for name in picks:
            part = series_for(name)
            part["school"] = name
            frames.append(part)
        combined = pd.concat(frames, ignore_index=True)

        span = st.slider(
            "Editions",
            int(combined["edition"].min()), int(combined["edition"].max()),
            (max(2004, int(combined["edition"].min())), int(combined["edition"].max())),
        )
        combined = combined[combined["edition"].between(*span)]

        if combined.empty:
            st.info("No ordinal ranks for those schools in that range.")
        else:
            st.altair_chart(rank_chart(combined, color_field="school", height=420),
                            width="stretch")
            wide = combined.pivot_table(index="school", columns="edition", values="rank")
            st.dataframe(wide, width="stretch")
            st.caption(
                "Blank cells mean the school was not ordinally ranked in that edition — "
                "it was in a tier, outside the published list, or classified in a "
                "different category. Category membership changes over time, so a gap is "
                "not necessarily a decline."
            )
    else:
        st.info("Pick at least one school.")

# --- Institution profile ------------------------------------------------------

with tab_home:
    # meta always exists; row only exists for schools with at least one ordinal rank.
    meta = LONG[LONG["school"] == focus].iloc[0]
    summary_rows = SUMMARY[SUMMARY["school"] == focus]
    row = summary_rows.iloc[0] if len(summary_rows) else None
    pub = series_for(focus)
    n_ranked = len(pub)

    st.subheader(f"{focus} · rank history")
    if row is not None:
        st.caption(
            f"{meta['category']} · {meta['state']} · {meta['control']} · ordinally ranked "
            f"in {int(row['editions'])} editions ({int(row['first_edition'])}–"
            f"{int(row['last_edition'])})"
        )
    else:
        st.caption(f"{meta['category']} · {meta['state']} · {meta['control']} · "
                   "tier years only")

    if n_ranked == 0:
        st.info(
            f"{focus} appears in the dataset only in tier or quartile years, so there is "
            "no ordinal series to chart. The table below lists every edition."
        )
    else:
        latest = int(pub.iloc[-1]["rank"])
        prior = int(pub.iloc[-2]["rank"]) if n_ranked > 1 else None

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"Latest published ({int(row['last_edition'])})", latest,
                  None if prior is None else f"{prior - latest:+d}")
        m2.metric("Best ever", int(row["best"]),
                  f"{int(row['best_edition'])} edition", delta_color="off")
        m3.metric("Worst ever", int(row["worst"]), delta_color="off")
        m4.metric("Total swing", int(row["swing"]),
                  help="Worst minus best. A large swing means the rank is volatile.")

        lo, hi = pub["rank"].min(), pub["rank"].max()
        band = alt.Scale(domain=[max(1, lo - 6), hi + 6], reverse=True)
        line = (
            alt.Chart(pub)
            .mark_line(strokeWidth=2.5, color="#5B2A86")
            .encode(x=alt.X("edition:O", axis=alt.Axis(labelAngle=0), title="Edition"),
                    y=alt.Y("rank:Q", scale=band, title="Rank (lower is better)"))
        )
        pts = (
            alt.Chart(pub).mark_point(size=70, filled=True, color="#5B2A86").encode(
                x="edition:O",
                y=alt.Y("rank:Q", scale=band),
                tooltip=["edition:O", "rank:Q"],
            )
        )
        st.altair_chart((line + pts).properties(height=380), width="stretch")

        if n_ranked > 1:
            st.caption(
                f"Best position: #{int(row['best'])} in the {int(row['best_edition'])} "
                f"edition. Worst: #{int(row['worst'])}. The {int(row['swing'])}-place swing "
                f"across {int(row['editions'])} editions is the volatility to keep in mind "
                "when reading any single year as a trend."
            )

    st.divider()
    left, right = st.columns([2, 3])

    with left:
        st.markdown("#### Every edition")
        hist = (
            LONG[LONG["school"] == focus][["edition", "rank", "tier", "change"]]
            .sort_values("edition", ascending=False)
        )
        hist["value"] = hist.apply(
            lambda r: str(int(r["rank"])) if pd.notna(r["rank"]) else r["tier"], axis=1
        )
        st.dataframe(
            hist[["edition", "value", "change"]],
            width="stretch", hide_index=True, height=430,
            column_config={
                "edition": st.column_config.NumberColumn("Edition", format="%d"),
                "value": st.column_config.TextColumn("Rank / tier"),
                "change": st.column_config.NumberColumn("1-yr", format="%+d"),
            },
        )

    with right:
        peers = (
            LONG[(LONG["state"] == meta["state"]) & (LONG["cat_key"] == meta["cat_key"])
                 & (LONG["edition"] == edition) & LONG["rank"].notna()]
            .sort_values("rank")[["school", "rank", "change"]]
            .reset_index(drop=True)
        )
        st.markdown(f"#### {meta['state']} · {meta['category']}, {edition} edition")
        if peers.empty:
            st.info(f"No {meta['state']} schools ranked in this category in {edition}.")
        else:
            peers.index += 1
            position = peers.index[peers["school"] == focus]
            st.dataframe(
                peers, width="stretch",
                column_config={
                    "school": st.column_config.TextColumn("School", width="large"),
                    "rank": st.column_config.NumberColumn(f"{edition} rank", format="%d"),
                    "change": st.column_config.NumberColumn("1-yr", format="%+d"),
                },
            )
            if len(position):
                st.caption(
                    f"**{focus} is {position[0]} of {len(peers)}** among ranked "
                    f"{meta['state']} schools in this category for the {edition} edition."
                )
            else:
                st.caption(
                    f"{focus} was not ranked in the {edition} edition, so it does not "
                    "appear in this list."
                )
            st.caption(
                "Category membership is not stable over time. Schools are reclassified "
                "between the national and regional pools as their degree mix changes, so "
                "a peer list drawn for one edition will not match another. Change the "
                "edition in the sidebar to see how this group has shifted."
            )

st.divider()
st.caption(
    "Ordinal rank series compiled by Andrew G. Reiter, *U.S. News & World Report "
    "Historical Liberal Arts College and University Rankings*. Sector classification from "
    "IPEDS HD2023. Full source list in the sidebar and in SOURCES.md."
)
