"""Route downloaded minutes through Datalab: OCR (/convert) then structured extraction (/extract).

Two billed steps per document:

1. **convert** — `mode=balanced` OCR to markdown, with `save_checkpoint=true`. The
   markdown is committed under `data/interim/datalab/markdown/` (small, diffable,
   and re-usable by any future extractor); the checkpoint lets step 2 skip re-parsing.
2. **extract** — the schema in `scripts/extraction_schema.py`, `extraction_mode=balanced`
   (per-field citations + independent verification) by default; `fast` is ~7x cheaper
   and is run alongside on the sample so the full-run mode is chosen on measured
   accuracy. Results are kept under `data/interim/datalab/extract/<mode>/` with their
   citations and verification metadata so they can be audited.

Every job appends a row to `data/interim/datalab/runs.csv` with page count and the
billed cost from `cost_breakdown`, which is what the cost projection in
`scripts/audit.py` is built from. Both steps skip documents already done.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from scripts.config import (
    DATALAB_BASE,
    DATALAB_CONVERT_MODE,
    DATALAB_EXTRACT,
    DATALAB_EXTRACTION_MODE,
    DATALAB_MARKDOWN,
    DATALAB_MIN_INTERVAL_S,
    DATALAB_POLL_S,
    DATALAB_RUNS_CSV,
    LF_DIR,
    MANIFEST_CSV,
    SAMPLE_CSV,
)
from scripts.extraction_schema import SCHEMA_VERSION, schema_json

log = logging.getLogger(__name__)

RUN_FIELDS = ["entry_id", "step", "request_id", "status", "mode", "page_count", "cost_cents",
              "cost_breakdown", "parse_quality_score", "runtime_s", "schema_version", "finished_utc",
              "error"]


class _RateLimiter:
    """One shared gate so polls from every worker stay under the per-minute cap."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.lock = threading.Lock()
        self.last = 0.0

    def wait(self) -> None:
        with self.lock:
            gap = time.monotonic() - self.last
            if gap < self.interval:
                time.sleep(self.interval - gap)
            self.last = time.monotonic()


_gate = _RateLimiter(DATALAB_MIN_INTERVAL_S)
_runs_lock = threading.Lock()


def _headers() -> dict[str, str]:
    key = os.environ.get("DATALAB_API_KEY")
    if not key:
        raise RuntimeError("Set DATALAB_API_KEY")
    return {"X-API-Key": key}


def _call(method: str, url: str, **kw: Any) -> dict[str, Any]:
    for attempt in range(6):
        _gate.wait()
        try:
            r = requests.request(method, url, headers=_headers(), timeout=180, **kw)
        except requests.RequestException as exc:
            log.warning("datalab %s failed: %s", url, exc)
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            log.warning("datalab %s → %s; backing off", url, r.status_code)
            time.sleep(30 * (attempt + 1))
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"datalab {r.status_code}: {r.text[:400]}")
        return r.json()
    raise RuntimeError(f"datalab {method} {url} kept failing")


def _submit_and_wait(endpoint: str, data: dict[str, Any], pdf: Path | None) -> dict[str, Any]:
    files = None
    fh = None
    if pdf is not None:
        fh = pdf.open("rb")
        files = {"file": (pdf.name, fh, "application/pdf")}
    try:
        job = _call("POST", DATALAB_BASE + endpoint, data=data, files=files)
    finally:
        if fh:
            fh.close()
    check = job["request_check_url"]
    started = time.monotonic()
    while True:
        time.sleep(DATALAB_POLL_S)
        res = _call("GET", check)
        if res.get("status") == "complete" or res.get("success") is False or res.get("status") == "failed":
            break
        if time.monotonic() - started > 1800:
            raise RuntimeError(f"{endpoint} job {job.get('request_id')} timed out")
    if res.get("result_url"):
        dl = requests.get(res["result_url"], timeout=120)
        dl.raise_for_status()
        res = {**dl.json(), **{k: v for k, v in res.items() if v is not None}}
    res["_request_id"] = job.get("request_id")
    return res


def _cost_cents(res: dict[str, Any]) -> float | None:
    cb = res.get("cost_breakdown") or {}
    for k in ("final_cost_cents", "total_cost_cents", "cost_cents"):
        if isinstance(cb.get(k), (int, float)):
            return float(cb[k])
    if isinstance(res.get("total_cost"), (int, float)):
        return float(res["total_cost"]) * 100
    return None


def _log_run(entry_id: int, step: str, res: dict[str, Any], mode: str, error: str = "") -> None:
    row = {
        "entry_id": entry_id, "step": step, "request_id": res.get("_request_id"),
        "status": res.get("status"), "mode": mode, "page_count": res.get("page_count"),
        "cost_cents": _cost_cents(res), "cost_breakdown": json.dumps(res.get("cost_breakdown")),
        "parse_quality_score": res.get("parse_quality_score"), "runtime_s": res.get("runtime"),
        "schema_version": SCHEMA_VERSION if step == "extract" else "",
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"), "error": error,
    }
    with _runs_lock:
        new = not DATALAB_RUNS_CSV.exists()
        DATALAB_RUNS_CSV.parent.mkdir(parents=True, exist_ok=True)
        with DATALAB_RUNS_CSV.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=RUN_FIELDS)
            if new:
                w.writeheader()
            w.writerow(row)


# ── document selection ──────────────────────────────────────────────────────

def _targets(scope: str, limit: int | None, entry_ids: list[int] | None) -> pd.DataFrame:
    man = pd.read_csv(MANIFEST_CSV)
    if scope == "sample":
        ids = pd.read_csv(SAMPLE_CSV)["entry_id"]
        man = man[man["entry_id"].isin(ids)]
    if entry_ids:
        man = man[man["entry_id"].isin(entry_ids)]
    man = man.sort_values("entry_id")
    return man.head(limit) if limit else man


def _md_path(row: pd.Series) -> Path:
    return DATALAB_MARKDOWN / str(row["year_folder"]) / f"{row['entry_id']}.md"


def _meta_path(row: pd.Series) -> Path:
    return DATALAB_MARKDOWN / str(row["year_folder"]) / f"{row['entry_id']}.convert.json"


def _extract_path(row: pd.Series, mode: str) -> Path:
    return DATALAB_EXTRACT / mode / str(row["year_folder"]) / f"{row['entry_id']}.json"


# ── step 1: convert ─────────────────────────────────────────────────────────

def convert_one(row: pd.Series) -> str:
    md, meta = _md_path(row), _meta_path(row)
    if md.exists() and meta.exists():
        return "skipped"
    pdf = LF_DIR / row["local_path"]
    data = {"output_format": "markdown", "mode": DATALAB_CONVERT_MODE,
            "paginate": "true", "save_checkpoint": "true"}
    try:
        res = _submit_and_wait("convert", data, pdf)
    except Exception as exc:  # noqa: BLE001
        _log_run(int(row["entry_id"]), "convert", {}, DATALAB_CONVERT_MODE, error=str(exc))
        raise
    if res.get("success") is False or not res.get("markdown"):
        _log_run(int(row["entry_id"]), "convert", res, DATALAB_CONVERT_MODE,
                 error=str(res.get("error") or "empty markdown"))
        raise RuntimeError(f"convert failed for {row['entry_id']}: {res.get('error')}")
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(res["markdown"])
    meta.write_text(json.dumps({k: res.get(k) for k in (
        "_request_id", "checkpoint_id", "page_count", "parse_quality_score", "runtime",
        "cost_breakdown", "metadata")} | {"mode": DATALAB_CONVERT_MODE}, indent=1, default=str))
    _log_run(int(row["entry_id"]), "convert", res, DATALAB_CONVERT_MODE)
    return "converted"


# ── step 2: extract ─────────────────────────────────────────────────────────

def extract_one(row: pd.Series, mode: str = DATALAB_EXTRACTION_MODE) -> str:
    out = _extract_path(row, mode)
    if out.exists() and json.loads(out.read_text()).get("schema_version") == SCHEMA_VERSION:
        return "skipped"
    data = {"page_schema": schema_json(), "extraction_mode": mode}
    pdf: Path | None = None
    meta = _meta_path(row)
    checkpoint = json.loads(meta.read_text()).get("checkpoint_id") if meta.exists() else None
    if checkpoint:
        data["checkpoint_id"] = checkpoint
    else:
        pdf = LF_DIR / row["local_path"]
        data["mode"] = DATALAB_CONVERT_MODE
    try:
        res = _submit_and_wait("extract", data, pdf)
        if res.get("success") is False and checkpoint:
            # Checkpoints expire; fall back to sending the file (re-parses, costs more)
            log.info("checkpoint for %s rejected (%s); re-sending file", row["entry_id"], res.get("error"))
            data.pop("checkpoint_id")
            data["mode"] = DATALAB_CONVERT_MODE
            res = _submit_and_wait("extract", data, LF_DIR / row["local_path"])
    except Exception as exc:  # noqa: BLE001
        _log_run(int(row["entry_id"]), "extract", {}, mode, error=str(exc))
        raise
    extracted = res.get("extraction_schema_json")
    if isinstance(extracted, str):
        try:
            extracted = json.loads(extracted)
        except json.JSONDecodeError:
            pass
    if res.get("success") is False or not extracted:
        _log_run(int(row["entry_id"]), "extract", res, mode,
                 error=str(res.get("error") or "empty extraction"))
        raise RuntimeError(f"extract failed for {row['entry_id']}: {res.get('error')}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "entry_id": int(row["entry_id"]), "schema_version": SCHEMA_VERSION,
        "extraction_mode": mode, "request_id": res.get("_request_id"),
        "page_count": res.get("page_count"), "cost_breakdown": res.get("cost_breakdown"),
        "extraction": extracted,
    }, indent=1, ensure_ascii=False))
    _log_run(int(row["entry_id"]), "extract", res, mode)
    return "extracted"


def _run(fn, scope: str, limit: int | None, entry_ids: list[int] | None, workers: int = 3,
         **kw: Any) -> int:
    rows = [r for _, r in _targets(scope, limit, entry_ids).iterrows()]
    counts: dict[str, int] = {}
    errors = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fn, r, **kw): r["entry_id"] for r in rows}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                status = fut.result()
                counts[status] = counts.get(status, 0) + 1
            except Exception as exc:  # noqa: BLE001
                errors += 1
                log.error("%s %s failed: %s", fn.__name__, futs[fut], exc)
            if i % 10 == 0:
                log.info("%s: %s/%s done %s errors=%s", fn.__name__, i, len(rows), counts, errors)
    print(f"{fn.__name__}: {counts} errors={errors}")
    return 0 if errors == 0 else 1


def convert_all(scope: str = "sample", limit: int | None = None,
                entry_ids: list[int] | None = None) -> int:
    return _run(convert_one, scope, limit, entry_ids)


def extract_all(scope: str = "sample", limit: int | None = None,
                entry_ids: list[int] | None = None, mode: str = DATALAB_EXTRACTION_MODE) -> int:
    return _run(extract_one, scope, limit, entry_ids, mode=mode)
