"""Filesystem paths and HTTP defaults shared by every stage."""

from __future__ import annotations

from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA_ORIGINAL = DATA / "original"
DATA_INTERIM = DATA / "interim"
DATA_PROCESSED = DATA / "processed"
DATA_AUDIT = DATA / "audit"
DATA_LOOKUPS = DATA / "lookups"
DOCS = ROOT / "docs"

for _p in (DATA_ORIGINAL, DATA_INTERIM, DATA_PROCESSED, DATA_AUDIT, DATA_LOOKUPS, DOCS):
    _p.mkdir(parents=True, exist_ok=True)

# Laserfiche originals: raw folder listings (JSON) and the PDFs themselves (Git LFS)
LF_DIR = DATA_ORIGINAL / "laserfiche"
LF_LISTINGS = LF_DIR / "listings"
LF_PDF = LF_DIR / "pdf"
INVENTORY_CSV = LF_DIR / "inventory.csv"  # every document discovered under Signed Minutes
MANIFEST_CSV = LF_DIR / "manifest.csv"  # every PDF downloaded: hash, bytes, method

# Datalab outputs: OCR markdown and raw extraction JSON, one file per document
DATALAB_DIR = DATA_INTERIM / "datalab"
DATALAB_MARKDOWN = DATALAB_DIR / "markdown"
DATALAB_EXTRACT = DATALAB_DIR / "extract"
DATALAB_RUNS_CSV = DATALAB_DIR / "runs.csv"  # one row per API job: pages, cost, mode

SAMPLE_CSV = DATA_LOOKUPS / "sample_quarterly.csv"
GOLD_JSON = DATA_LOOKUPS / "gold" / "hand_transcribed_2021_2022.json"
MEMBER_ALIASES_CSV = DATA_LOOKUPS / "member_aliases.csv"
PROVENANCE_CSV = DATA_PROCESSED / "provenance.csv"

# ─── Laserfiche WebLink ─────────────────────────────────────────────────────

PORTAL = "https://documents.bouldercolorado.gov/WebLink/"
REPO = "LF8PROD2"
SIGNED_MINUTES_FOLDER_ID = 10888  # \Central Records\City Council\Signed Minutes

# Boulder's server omits its intermediate certificate. This bundle is certifi's roots
# plus that intermediate (from the CU Info Science Web Data Science Book, ch. 9); see
# certs/make_ca_bundle.py to rebuild it. Never pass verify=False.
CA_BUNDLE = ROOT / "certs" / "boulder-ca-bundle.pem"

USER_AGENT = (
    "BoulderPublicData-City-Council-Minutes/0.2 "
    "(civic data research; https://github.com/BoulderPublicData/City-Council-Minutes)"
)
REQUEST_TIMEOUT_S = 90

# The server stops answering after ~13-17 requests in a row and recovers after a
# five-minute pause (observed by the textbook authors, Oct 2026). We pace requests,
# take a proactive break every BURST requests, and back off on any failure.
LF_MIN_INTERVAL_S = 4.0
LF_BURST = 12
LF_BURST_PAUSE_S = 310
LF_FAILURE_PAUSE_S = 330

# ─── Datalab ────────────────────────────────────────────────────────────────

DATALAB_BASE = "https://www.datalab.to/api/v1/"
DATALAB_CONVERT_MODE = "balanced"  # lite | fast | balanced | accurate
DATALAB_EXTRACTION_MODE = "balanced"  # turbo | fast | balanced | accurate
# Free tier: 10 requests/minute and 5 concurrent jobs. Status polls count as requests,
# so slow jobs (balanced extraction, ~2-3 min) are polled less often; a 429 backs off.
DATALAB_POLL_S = 5
DATALAB_POLL_SLOW_S = 20
DATALAB_MIN_INTERVAL_S = 3
DATALAB_WORKERS = 5
