# Sources

Every figure in this dashboard traces to one of the following. Nothing else is used —
no IPEDS survey data, no Common Data Set extracts, no internal institutional-research
figures.

## Ranking series (all years, all schools)

**Andrew G. Reiter, "U.S. News & World Report Historical Liberal Arts College and
University Rankings"** — <https://www.andyreiter.com/datasets/>

Two workbooks, both included in `data/`:

| File | Coverage |
|---|---|
| `US-News-Liberal-Arts-Through-2026.xlsx` | National Liberal Arts Colleges, 1985–2026 |
| `US-News-National-Universities-Top150-Through-2026.xlsx` | National Universities, top 150, 1984–2026 |

`data/rankings.json` is the flattened merge of these two workbooks, keyed by school with
one entry per edition. It carries IPEDS unit IDs so the series can be joined to other
datasets later.

## Ranking context and edition timing

- **U.S. News — The 2026 Best Colleges Rankings Are Out**
  <https://www.usnews.com/education/best-colleges/articles/us-news-ranks-best-colleges>
  Confirms the 2026 edition is the current published edition (released September 2025).

- **U.S. News — Beyond First-Time, Full-Time Students: Updates to the 2027 College Data
  Collection**
  <https://www.usnews.com/education/blogs/college-rankings-blog/articles/2026-05-13/beyond-first-time-full-time-students-updates-to-the-2027-college-data-collection>
  Confirms the 2027 edition timing and that institutions may be placed in different
  ranking categories for 2027.

- **U.S. News — 2026 Best National Liberal Arts Colleges**
  <https://www.usnews.com/best-colleges/rankings/national-liberal-arts-colleges>
  The published 2026 category list.

## Sector (public / private) classification

**IPEDS Institutional Characteristics, HD2023** —
<https://nces.ed.gov/ipeds/datacenter/data/HD2023.zip> (stored as `data/IPEDS_HD2023.csv`)

The Reiter workbooks carry school name, state, IPEDS unit id and ranks — but no control
field, which is why the dashboard originally had no way to tell a public institution from
a private one. The `CONTROL` column from IPEDS is joined on unit id to supply it:

| CONTROL | Label | Schools in dataset |
|---|---|---|
| 1 | Public | 144 |
| 2 | Private not-for-profit | 401 |
| 3 | Private for-profit | 1 |
| — | Unknown | 25 |

The 25 unknowns are institutions that no longer appear in the IPEDS directory — almost
all closed (Atlantic Union College, Barat College, Barber Scotia College, Burlington
College, Clearwater Christian College and similar). They were ranked historically, so
they stay in the series.

For-profit institutions are effectively absent from these two national categories, which
is a fact about how U.S. News classifies rather than a gap in this data.

## Known coverage gaps

- **Regional Universities** and **Regional Colleges** are not included. No multi-year
  public dataset exists for those categories, so many small private colleges that
  describe themselves as liberal arts institutions do not appear here at all.
- The National Universities workbook covers the **top 150 only**. A missing year for a
  national university can mean "fell outside the top 150," not "unranked."
- Liberal arts editions **before 2004** used tiers and quartiles rather than ordinal
  positions. Those values are preserved as text bands and excluded from all arithmetic.
- **Category membership is not stable across years.** Schools move between national and
  regional pools, which changes the field a rank is measured against. A rank series is
  not a like-for-like comparison over long spans.
