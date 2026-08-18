# U.S. News College Ranking Dashboard

Rank history for every ordinally ranked National University and National Liberal Arts
College, 1984-2026.

## Run

```
cd F:\USNewsRankingDashboard
streamlit run app.py
```

Opens at http://localhost:8501

## Tabs

- **Explorer** - filter by edition, category, state and name; sortable table with
  1-year change, best-ever and worst-ever; CSV export of the current view.
- **Compare schools** - overlay up to 12 rank histories on one reversed axis.
  Defaults to the Michigan liberal arts group.

## Reading the numbers

Lower is better. A positive 1-year change means the school moved up.

Pre-2004 liberal arts editions used tiers and quartiles, not ordinal positions; those
years show a band and are excluded from all arithmetic. The national universities file
covers the top 150 only, so a missing year may mean "fell outside the top 150" rather
than "unranked". Category membership changes over time, so long rank series are not
strictly like-for-like.

## Files

```
app.py                 Streamlit app
requirements.txt       Dependencies
data/rankings.json     Flattened rank series used by the app
data/*.xlsx            Reiter source workbooks
```

## Updating after the 2027 edition publishes (September 2026)

1. Download the refreshed Reiter workbooks into `data/`.
2. Rebuild `data/rankings.json` from them.
3. In `app.py`, bump `LATEST_PUBLIC` to 2027.
