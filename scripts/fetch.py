"""Download minutes PDFs into `data/original/laserfiche/pdf/<year>/<entry_id>.pdf`.

Idempotent: a document already in the manifest with its file on disk is skipped.

Documents are fetched in batches through the portal's bulk ZIP export (one PDF per
entry, named after the entry), which costs a handful of requests per batch rather
than ~3 per scanned record. Anything the export doesn't return, or whose name is
ambiguous within its batch, falls back to a per-entry download.

`manifest.csv` records, per file, the portal entry, how it was obtained
(`zip_export`; or per entry, `electronic_file` = the attached PDF and
`generate_pdf10` = rendered from scanned page images by the viewer), its SHA-256,
size, and page count. PDFs rendered from page images get new bytes on every
download, so for those the page count — not the hash — is the identity check
against the inventory.

Originals are immutable once fetched: nothing downstream edits these files.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import re
from datetime import UTC, datetime

import pandas as pd
from pypdf import PdfReader

from scripts.config import INVENTORY_CSV, LF_DIR, LF_PDF, MANIFEST_CSV, SAMPLE_CSV
from scripts.gold import gold_entry_ids
from scripts.laserfiche import LaserficheClient, LaserficheError, docview_url

log = logging.getLogger(__name__)

MANIFEST_FIELDS = ["entry_id", "year_folder", "name", "local_path", "method", "bytes", "sha256",
                   "pdf_pages", "inventory_pages", "source_url", "fetched_utc"]
ZIP_BATCH = 25


def _targets(scope: str, limit: int | None, entry_ids: list[int] | None) -> pd.DataFrame:
    inv = pd.read_csv(INVENTORY_CSV)
    if scope == "sample":
        inv = inv[inv["entry_id"].isin(pd.read_csv(SAMPLE_CSV)["entry_id"])]
    elif scope == "gold":
        inv = inv[inv["entry_id"].isin(gold_entry_ids())]
    if entry_ids:
        inv = inv[inv["entry_id"].isin(entry_ids)]
    return inv.head(limit) if limit else inv


def name_key(name: str) -> str:
    """Compare entry names with ZIP member names, which drop the extension and
    may replace characters Windows forbids in filenames."""
    stem = re.sub(r"\.pdf$", "", name.rsplit("/", 1)[-1], flags=re.IGNORECASE)
    return re.sub(r"[^0-9a-z]", "", stem.lower())


def _save(row, content: bytes, method: str, client: LaserficheClient) -> None:
    pages = None if pd.isna(row.page_count) else int(row.page_count)
    year = "unknown" if pd.isna(row.year_folder) else str(int(row.year_folder))
    dest = LF_PDF / year / f"{row.entry_id}.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    try:
        pdf_pages = len(PdfReader(io.BytesIO(content)).pages)
    except Exception:  # noqa: BLE001
        pdf_pages = None
    if pages and pdf_pages and pdf_pages != pages:
        log.warning("entry %s: PDF has %s pages, portal lists %s", row.entry_id, pdf_pages, pages)
    new = not MANIFEST_CSV.exists()
    with MANIFEST_CSV.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        if new:
            w.writeheader()
        w.writerow({
            "entry_id": row.entry_id, "year_folder": year, "name": row.name,
            "local_path": str(dest.relative_to(LF_DIR)), "method": method,
            "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
            "pdf_pages": pdf_pages, "inventory_pages": pages,
            "source_url": docview_url(int(row.entry_id)),
            "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        })
    log.info("%s %s via %s (%s pages, %s KB) [%s portal requests]", row.entry_id, row.name,
             method, pdf_pages, len(content) // 1024, client.requests_made)


def _fetch_one(row, client: LaserficheClient) -> bool:
    pages = None if pd.isna(row.page_count) else int(row.page_count)
    try:
        content, method = client.download_pdf(int(row.entry_id), bool(row.is_edoc), pages)
    except LaserficheError as exc:
        log.error("entry %s (%s): %s", row.entry_id, row.name, exc)
        return False
    _save(row, content, method, client)
    return True


def _fetch_batch(rows: list, client: LaserficheClient) -> int:
    """Fetch a batch through the ZIP export; return the number of errors."""
    keys = [name_key(r.name) for r in rows]
    unique = [r for r, k in zip(rows, keys, strict=True) if keys.count(k) == 1]
    leftovers = [r for r in rows if r not in unique]
    if unique:
        try:
            files = client.export_zip([int(r.entry_id) for r in unique])
        except (LaserficheError, OSError, ValueError) as exc:
            log.warning("zip export of %s entries failed (%s); fetching one by one", len(unique), exc)
            files = {}
        by_key = {name_key(fn): content for fn, content in files.items()}
        for r in unique:
            content = by_key.get(name_key(r.name))
            if content and content[:5] == b"%PDF-":
                _save(r, content, "zip_export", client)
            else:
                leftovers.append(r)
    errors = 0
    for r in leftovers:
        errors += not _fetch_one(r, client)
    return errors


def fetch(scope: str = "sample", limit: int | None = None,
          entry_ids: list[int] | None = None) -> int:
    targets = _targets(scope, limit, entry_ids)
    done: set[int] = set()
    if MANIFEST_CSV.exists():
        man = pd.read_csv(MANIFEST_CSV)
        done = {int(r.entry_id) for r in man.itertuples() if (LF_DIR / r.local_path).exists()}
    todo = list(targets[~targets["entry_id"].isin(done)].itertuples())
    print(f"fetch: {len(targets)} targets, {len(targets) - len(todo)} already on disk, "
          f"{len(todo)} to download")
    client = LaserficheClient()
    errors = 0
    for start in range(0, len(todo), ZIP_BATCH):
        batch = todo[start:start + ZIP_BATCH]
        errors += _fetch_batch(batch, client)
        log.info("[%s/%s] fetched [%s portal requests]", min(start + ZIP_BATCH, len(todo)),
                 len(todo), client.requests_made)
    print(f"fetch: {len(todo) - errors} downloaded, {errors} errors")
    return 0 if errors == 0 else 1
