# Data Engineering: Pipeline, Quality and Gold Snapshot Reconciliation

## Architecture

The existing application consumes the same Gold CSV whether or not snapshot
reconciliation is enabled.

```mermaid
flowchart LR
    N[Numbeo rankings] --> B[Bronze CSV]
    S[Stack Overflow 2024 survey] --> B
    W[World Bank metadata] --> B
    E[Current exchange rates] --> B
    B --> C[Silver: clean and standardize]
    C --> G[Gold: country affordability CSV]
    G --> A[Streamlit dashboard]
    G -. optional --track-snapshots .-> H[Content-addressed snapshot history]
    H --> Q[Delta counters in quality summary]
```

The four sources are **full extracts**, not change-data-capture feeds. Numbeo is
queried for a selected ranking year; the Stack Overflow dataset currently stays
fixed to its 2024 developer survey, and exchange rates are fetched at run time.
Consequently, re-running the same Numbeo year on a later day may yield different
USD salaries due to exchange-rate changes. **Do not interpret these differences
as a longitudinal trend in developer purchasing power.**

## Running

Default behavior is unchanged:

```bash
python -m src.pipeline --year 2024
```

To keep an **optional audit of changes between full Gold snapshots**:

```bash
python -m src.pipeline --year 2024 --track-snapshots
```

On successful runs, this creates:

```text
data/snapshots/
  2024/
    latest.json                  # latest snapshot ID, UTC ingestion time, change counts
    history/
      <sha256>.csv                # full snapshot, sorted by ISO3, fixed numeric precision
data/gold/
  country_affordability.csv       # UNCHANGED Streamlit contract
  pipeline_run_summary.json      # optional snapshot statistics when flag is enabled
```

These are **local generated artifacts** and intentionally gitignored. Do not
commit personal, proprietary or unlicensed source data to the repository.

## Reconciliation semantics

- Country identity uses **World Bank ISO3** rather than the display name.
- For a given Numbeo ranking year, each full Gold result is validated (required
  columns, unique nonblank keys, finite numeric values, positive cost index).
- Data is sorted by ISO3 and numeric fields are rounded to eight decimal places
  before content hashing, to avoid changes caused solely by row order.
- The content SHA-256 identifies the full snapshot. Running identical data twice
  produces the same ID and **does not** write a second history file or manifest.
- Rows are classified as **inserted**, **updated**, **unchanged** or **removed**
  relative to the preceding *snapshot for that same year*.
- A removed country is **not physically deleted from the archived snapshot**;
  the earlier full snapshot remains accessible.
- A missing or corrupted previous snapshot raises an explicit error instead
  of silently replacing historical data.
- Archived files and the pointer manifest use atomic replacement.
- The collection is **not** a database transaction across every CSV and JSON.
  Avoid running concurrent pipeline processes targeting the same snapshot root.

This is **snapshot comparison**, not incremental API ingestion, not a Delta
Lake implementation, and not SCD Type 2. The Bronze and Silver stages still
fetch/process the full source data on each run. It improves auditability and
idempotent history management without changing the dashboard schema.

## Quality and failure behavior

The existing pipeline summary records input, cleaned and Gold row counts,
unmatched countries, currency errors and other quality metrics. When
`--track-snapshots` is enabled, it additionally contains `snapshot` with:

```json
{
  "status": "updated",
  "inserted": 1,
  "updated": 2,
  "unchanged": 91,
  "removed": 1,
  "snapshot_id": "<sha256>",
  "previous_snapshot_id": "<sha256>"
}
```

The numbers above are **illustrative schema values**, not observed execution
metrics. Refer to the generated summary for actual run results.

When source fetching fails before Gold is computed, snapshot reconciliation
does not run. The offline test suite includes initial/identical/reordered runs,
added/modified/removed countries, corrupted archives, invalid keys/values,
year isolation, the optional CLI and summary schema.

## Test commands

```bash
python -m pytest -q
ruff check .
```

The tests use in-memory and temporary fixture data; they do not require access
to the source APIs. For changes to Streamlit layout, verify the application
separately. This work intentionally does **not** change `app.py` or its CSS.
