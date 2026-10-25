"""A polite client for Boulder's Laserfiche WebLink 11 portal.

Three things the portal does that a naive scraper trips over:

1. **Certificates.** The server omits its intermediate certificate, so every request
   verifies against `certs/boulder-ca-bundle.pem` (see `config.CA_BUNDLE`).
2. **Rate limiting.** It stops answering after a burst of ~15 requests and recovers
   after about five minutes. `LaserficheClient` paces requests, pauses every
   `LF_BURST` requests, and on a failure waits out the block before retrying.
3. **Two kinds of record.** Recent minutes are *electronic documents* (a PDF file is
   attached) and download from `ElectronicFile.aspx`. Older minutes are *imaged
   documents* (scanned page images, no file); for those `ElectronicFile.aspx`
   answers 200 with an empty body, and the viewer instead builds a PDF on request:
   POST `GeneratePDF10.aspx` → poll `DocumentService.aspx/PDFTransition` → GET
   `PDF10/<key>/<docid>`. Those PDFs are rebuilt on every request, so their hashes
   change between downloads; compare page counts/images, not hashes.

The folder listing comes from the JSON endpoint the browse page itself calls,
`FolderListingService.aspx/GetFolderListing2`.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from scripts.config import (
    CA_BUNDLE,
    LF_BURST,
    LF_BURST_PAUSE_S,
    LF_FAILURE_PAUSE_S,
    LF_MIN_INTERVAL_S,
    PORTAL,
    REPO,
    REQUEST_TIMEOUT_S,
    USER_AGENT,
)

log = logging.getLogger(__name__)

FOLDER = 0  # entry["type"] for a folder


class LaserficheError(RuntimeError):
    pass


class LaserficheClient:
    def __init__(self, max_attempts: int = 4) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.max_attempts = max_attempts
        self._last = 0.0
        self._since_pause = 0
        self._has_viewer_session = False
        self.requests_made = 0

    # ── pacing ──────────────────────────────────────────────────────────────

    def _wait_turn(self) -> None:
        if self._since_pause >= LF_BURST:
            log.info("burst limit reached; pausing %ss", LF_BURST_PAUSE_S)
            time.sleep(LF_BURST_PAUSE_S)
            self._since_pause = 0
        gap = time.monotonic() - self._last
        if gap < LF_MIN_INTERVAL_S:
            time.sleep(LF_MIN_INTERVAL_S - gap)

    def _request(self, method: str, path: str, **kw: Any) -> requests.Response:
        kw.setdefault("timeout", REQUEST_TIMEOUT_S)
        kw["verify"] = str(CA_BUNDLE)
        last_exc: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            self._wait_turn()
            try:
                self._last = time.monotonic()
                self._since_pause += 1
                self.requests_made += 1
                r = self.session.request(method, PORTAL + path, **kw)
                if r.status_code in (429, 502, 503, 504):
                    raise LaserficheError(f"HTTP {r.status_code}")
                r.raise_for_status()
                return r
            except (requests.RequestException, LaserficheError) as exc:
                last_exc = exc
                log.warning("request failed (%s/%s) %s %s: %s; pausing %ss",
                            attempt, self.max_attempts, method, path, exc, LF_FAILURE_PAUSE_S)
                time.sleep(LF_FAILURE_PAUSE_S)
                self._since_pause = 0
                # A long block can invalidate the viewer session cookie
                self._has_viewer_session = False
        raise LaserficheError(f"{method} {path} failed after {self.max_attempts} attempts") from last_exc

    # ── listings ────────────────────────────────────────────────────────────

    def list_folder(self, folder_id: int, page_size: int = 200) -> dict[str, Any]:
        """Return the folder's listing, with every page of results concatenated."""
        results: list[dict[str, Any]] = []
        start = 0
        data: dict[str, Any] = {}
        while True:
            body = {"repoName": REPO, "folderId": folder_id, "getNewListing": True,
                    "start": start, "end": start + page_size,
                    "sortColumn": "", "sortAscending": True}
            r = self._request("POST", "FolderListingService.aspx/GetFolderListing2", json=body)
            data = r.json()["data"]
            results.extend(data["results"])
            start += page_size
            if start >= data["totalEntries"] or not data["results"]:
                break
        data["results"] = results
        return data

    # ── downloads ───────────────────────────────────────────────────────────

    def download_electronic(self, entry_id: int) -> bytes:
        r = self._request("GET", f"ElectronicFile.aspx?docid={entry_id}&dbid=0&repo={REPO}")
        return r.content

    def _ensure_viewer_session(self, entry_id: int) -> None:
        # GeneratePDF10 answers "Session lost" without the cookies DocView sets
        if not self._has_viewer_session:
            self._request("GET", f"DocView.aspx?id={entry_id}&dbid=0&repo={REPO}")
            self._has_viewer_session = True

    def generate_pdf(self, entry_id: int, page_count: int) -> bytes:
        """Have the viewer render an imaged document's pages into a PDF."""
        for attempt in range(2):
            self._ensure_viewer_session(entry_id)
            r = self._request(
                "POST",
                f"GeneratePDF10.aspx?key={entry_id}&PageRange=1-{page_count}&Watermark=0&repo={REPO}",
                data="{}", headers={"Content-Type": "application/json"},
            )
            key = r.text.split("\n", 1)[0].strip()
            if "Session lost" in r.text or len(key) != 36:
                self._has_viewer_session = False
                if attempt == 0:
                    continue
                raise LaserficheError(f"GeneratePDF10 refused entry {entry_id}: {r.text[:120]!r}")
            for _ in range(60):
                time.sleep(3)
                p = self._request("POST", "DocumentService.aspx/PDFTransition", json={"Key": key})
                status = p.json().get("data") or {}
                if status.get("finished"):
                    if not status.get("success"):
                        raise LaserficheError(f"PDF build failed for {entry_id}: {status.get('errMsg')}")
                    break
            else:
                raise LaserficheError(f"PDF build for {entry_id} never finished")
            return self._request("GET", f"PDF10/{key}/{entry_id}").content
        raise LaserficheError("unreachable")

    def download_pdf(self, entry_id: int, is_edoc: bool, pages: int | None) -> tuple[bytes, str]:
        """Return (pdf_bytes, method) for one document."""
        if is_edoc:
            content = self.download_electronic(entry_id)
            if content[:5] == b"%PDF-":
                return content, "electronic_file"
            log.info("entry %s: electronic file is not a PDF (%r); rendering pages",
                     entry_id, content[:12])
        content = self.generate_pdf(entry_id, max(int(pages or 1), 1))
        if content[:5] != b"%PDF-":
            raise LaserficheError(f"entry {entry_id}: rendered file is not a PDF")
        return content, "generate_pdf10"


def page_count(entry: dict[str, Any]) -> int | None:
    """The second item of a document entry's `data` is its page count."""
    data = entry.get("data") or []
    if len(data) > 1 and isinstance(data[1], int):
        return data[1]
    return None


def docview_url(entry_id: int) -> str:
    return f"{PORTAL}DocView.aspx?id={entry_id}&dbid=0&repo={REPO}"
