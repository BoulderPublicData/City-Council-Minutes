"""Download minutes PDFs into `data/original/laserfiche/pdf/<year>/<entry_id>.pdf`.

Idempotent: a document already in the manifest with its file on disk is skipped.
`manifest.csv` records, per file, the portal entry, how it was obtained
(`electronic_file` = the attached PDF; `generate_pdf10` = rendered from scanned
page images by the portal's viewer), its SHA-256, size, and page count. Rendered
PDFs get new bytes on every download, so for those the page count — not the hash —
is the identity check against the inventory.

Originals are immutable once fetched: nothing downstream edits these files.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
from datetime import UTC, datetime

import pandas as pd
from pypdf import PdfReader

from scripts.config import INVENTORY_CSV, LF_DIR, LF_PDF, MANIFEST_CSV, SAMPLE_CSV
from scripts.laserfiche import LaserficheClient, LaserficheError, docview_url

log = logging.getLogger(__name__)

MANIFEST_FIELDS = ["entry_id", "year_folder", "name", "local_path", "method", "bytes", "sha256",
                   "pdf_pages", "inventory_pages", "source_url", "fetched_utc"]


def _targets(scope: str, limit: int | None, entry_ids: list[int] | None) -> pd.DataFrame:
    inv = pd.read_csv(INVENTORY_CSV)
    if scope == "sample":
        inv = inv[inv["entry_id"].isin(pd.read_csv(SAMPLE_CSV)["entry_id"])]
    if entry_ids:
        inv = inv[inv["entry_id"].isin(entry_ids)]
    return inv.head(limit) if limit else inv


def fetch(scope: str = "sample", limit: int | None = None,
          entry_ids: list[int] | None = None) -> int:
    targets = _targets(scope, limit, entry_ids)
    done: set[int] = set()
    if MANIFEST_CSV.exists():
        man = pd.read_csv(MANIFEST_CSV)
        done = {int(r.entry_id) for r in man.itertuples() if (LF_DIR / r.local_path).exists()}
    todo = targets[~targets["entry_id"].isin(done)]
    print(f"fetch: {len(targets)} targets, {len(targets) - len(todo)} already on disk, "
          f"{len(todo)} to download")
    client = LaserficheClient()
    errors = 0
    for i, row in enumerate(todo.itertuples(), 1):
        pages = None if pd.isna(row.page_count) else int(row.page_count)
        try:
            content, method = client.download_pdf(int(row.entry_id), bool(row.is_edoc), pages)
        except LaserficheError as exc:
            errors += 1
            log.error("entry %s (%s): %s", row.entry_id, row.name, exc)
            continue
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
        log.info("[%s/%s] %s %s via %s (%s pages, %s KB) [%s portal requests]", i, len(todo),
                 row.entry_id, row.name, method, pdf_pages, len(content) // 1024,
                 client.requests_made)
    print(f"fetch: {len(todo) - errors} downloaded, {errors} errors")
    return 0 if errors == 0 else 1
