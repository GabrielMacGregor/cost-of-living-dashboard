"""Auditable, content-addressed Gold snapshots for full-refresh data sources.

This is snapshot reconciliation, NOT change-data-capture or incremental API ingestion.
Survey year and ingestion timestamp are separate: snapshots compare recomputations
of the same survey year, potentially using newer exchange rates.
"""

import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import config

# A refresh that drops more than this share of previously known countries is almost
# certainly an ingestion failure, not a real change. Refuse it instead of auditing it.
DEFAULT_MAX_REMOVED_FRACTION = 0.25

COLUMNS = (
    "iso3",
    "country",
    "region",
    "cost_of_living_index",
    "median_salary_usd",
    "affordability_index",
)
NUMERIC_COLUMNS = COLUMNS[3:]


def _canonical(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate one row per ISO3 country and normalize float precision for comparison."""
    if frame.columns.duplicated().any():
        raise ValueError("Gold snapshot contains duplicate column names")
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Gold snapshot missing columns: {sorted(missing)}")
    df = frame.loc[:, list(COLUMNS)].copy()
    for col in ("iso3", "country", "region"):
        if df[col].isna().any() or df[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"Gold snapshot has missing or blank {col}")
        df[col] = df[col].astype(str).str.strip()
    if df["iso3"].duplicated().any():
        raise ValueError("Gold snapshot contains duplicate iso3 keys")
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any() or not df[col].map(math.isfinite).all():
            raise ValueError(f"Gold snapshot contains invalid numeric values in {col}")
        df[col] = df[col].round(8)
    if (df["cost_of_living_index"] <= 0).any():
        raise ValueError("Gold snapshot cost_of_living_index must be positive")
    if (df["median_salary_usd"] < 0).any():
        raise ValueError("Gold snapshot median_salary_usd must be nonnegative")
    return df.sort_values("iso3", kind="stable").reset_index(drop=True)


def _csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, float_format="%.8f", lineterminator="\n").encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".tmp-", delete=False) as tmp:
            temp_name = tmp.name
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def _row_map(df: pd.DataFrame) -> dict:
    return {
        row["iso3"]: tuple(row[col] for col in COLUMNS[1:])
        for row in df.to_dict(orient="records")
    }


def reconcile_gold_snapshot(
    gold: pd.DataFrame,
    year: int,
    snapshot_root: Path = config.SNAPSHOT_DIR,
    max_removed_fraction: float | None = DEFAULT_MAX_REMOVED_FRACTION,
) -> dict:
    """Persist a full Gold snapshot only if content changed, reporting row-level deltas.

    The original Gold CSV contract stays unchanged. Files are stored per survey
    year and addressed by content hash; repeated identical runs do not write.
    Does not delete rows or historical snapshots when a country disappears.
    Every change also appends an immutable manifest under ``log/`` so the order,
    timestamps and deltas of past versions stay reconstructable (``latest.json`` is
    only a pointer to the newest one). A refresh that removes more than
    ``max_removed_fraction`` of the previous countries is refused; pass None to disable.
    """
    if not isinstance(year, int) or not 1900 <= year <= 2200:
        raise ValueError("survey year must be an integer between 1900 and 2200")
    if gold.empty:
        raise ValueError("Gold snapshot is empty; refusing to replace historical audit data")
    current = _canonical(gold)
    content = _csv_bytes(current)
    snapshot_id = hashlib.sha256(content).hexdigest()
    root = Path(snapshot_root) / str(year)
    manifest_path = root / "latest.json"
    previous_id = None
    previous = _canonical(current.iloc[0:0].copy())

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous_id = manifest["snapshot_id"]
            if not isinstance(previous_id, str) or not re.fullmatch(r"[0-9a-f]{64}", previous_id):
                raise ValueError("invalid previous snapshot id")
            previous_path = root / "history" / f"{previous_id}.csv"
            previous_bytes = previous_path.read_bytes()
            if hashlib.sha256(previous_bytes).hexdigest() != previous_id:
                raise ValueError("previous snapshot checksum mismatch")
            previous = _canonical(pd.read_csv(previous_path, dtype={"iso3": str}))
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"Previous snapshot is missing or corrupted: {exc}") from exc

    before, after = _row_map(previous), _row_map(current)
    before_keys, after_keys = set(before), set(after)
    common = before_keys & after_keys
    changes = {
        "inserted": len(after_keys - before_keys),
        "updated": sum(before[k] != after[k] for k in common),
        "unchanged": sum(before[k] == after[k] for k in common),
        "removed": len(before_keys - after_keys),
    }
    if (
        max_removed_fraction is not None
        and before_keys
        and changes["removed"] / len(before_keys) > max_removed_fraction
    ):
        raise ValueError(
            f"Gold snapshot would remove {changes['removed']} of {len(before_keys)} "
            f"previous countries (limit {max_removed_fraction:.0%}); refusing as a likely "
            "ingestion failure"
        )
    if previous_id == snapshot_id:
        return {"status": "unchanged", "snapshot_id": snapshot_id,
                "previous_snapshot_id": previous_id, **changes}

    history_path = root / "history" / f"{snapshot_id}.csv"
    if history_path.exists():
        if hashlib.sha256(history_path.read_bytes()).hexdigest() != snapshot_id:
            raise ValueError("Existing snapshot history checksum mismatch")
    else:
        _atomic_write(history_path, content)
    now = datetime.now(timezone.utc)
    metadata = {
        "schema_version": 1,
        "survey_year": year,
        "ingested_at_utc": now.isoformat(),
        "snapshot_id": snapshot_id,
        "previous_snapshot_id": previous_id,
        "changes": changes,
        "note": "Full-source snapshot comparison; not incremental source extraction.",
    }
    payload = (json.dumps(metadata, indent=2) + "\n").encode("utf-8")
    log_name = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{snapshot_id[:12]}.json"
    _atomic_write(root / "log" / log_name, payload)
    _atomic_write(manifest_path, payload)
    return {"status": "initial" if previous_id is None else "updated",
            "snapshot_id": snapshot_id, "previous_snapshot_id": previous_id, **changes}
