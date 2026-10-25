"""Walk the Signed Minutes folder tree and write `data/original/laserfiche/inventory.csv`.

Each folder's raw listing is cached as `listings/<folderId>.json`, so a re-run only
asks the portal for folders it has not seen (pass `refresh=True` to re-list
everything — needed to pick up newly filed minutes).

Folder layout changes over time: through ~2013 each year folder holds the minutes
directly ("Minutes - Apr-01-2003"); later years nest them in month folders
("01 JAN", "09 SEPT"). The walk is recursive so it does not depend on either.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from scripts.config import INVENTORY_CSV, LF_LISTINGS, SIGNED_MINUTES_FOLDER_ID
from scripts.laserfiche import FOLDER, LaserficheClient, docview_url, page_count

log = logging.getLogger(__name__)

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_name_date(name: str) -> date | None:
    """Best-effort meeting date from a document name; None when ambiguous."""
    s = name.strip()
    candidates: list[tuple[int, int, int]] = []
    for y, m, d in re.findall(r"(?<!\d)(\d{4}) ?[-._] ?(\d{1,2}) ?[-._] ?(\d{1,2})(?!\d)", s):
        candidates.append((int(y), int(m), int(d)))
    if not candidates:
        for mon, d, y in re.findall(r"([A-Za-z]{3,9})\.?[- ](\d{1,2})(?:st|nd|rd|th)?[-, ]+(\d{4})", s):
            if mon[:3].lower() in MONTHS:
                candidates.append((int(y), MONTHS[mon[:3].lower()], int(d)))
    if not candidates:
        for m, d, y in re.findall(r"(?<!\d)(\d{1,2})[-._](\d{1,2})[-._](\d{2}|\d{4})(?!\d)", s):
            yy = int(y)
            if yy < 100:
                yy += 2000 if yy < 70 else 1900
            candidates.append((yy, int(m), int(d)))
    for y, m, d in candidates:
        try:
            return date(y, m, d)
        except ValueError:
            continue
    return None


def name_meeting_type(name: str) -> str | None:
    """Meeting type when the document name says so; None otherwise (decided later)."""
    n = name.lower()
    for key, label in [("study session", "study_session"), ("retreat", "retreat"),
                       ("joint", "joint"), ("special", "special"), ("continued", "continued"),
                       ("adjourned", "adjourned"), ("executive session", "executive_session")]:
        if key in n:
            return label
    return None


def _listing(client: LaserficheClient, folder_id: int, refresh: bool) -> dict[str, Any]:
    path = LF_LISTINGS / f"{folder_id}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    data = client.list_folder(folder_id)
    data["_retrieved_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    log.info("listed %s (%s entries) [%s portal requests so far]",
             data.get("path"), data.get("totalEntries"), client.requests_made)
    return data


def walk(client: LaserficheClient, folder_id: int, refresh: bool,
         years: set[int] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    stack = [folder_id]
    while stack:
        fid = stack.pop()
        listing = _listing(client, fid, refresh=refresh)
        for e in listing["results"]:
            if e["type"] == FOLDER:
                if fid == folder_id and years and e["name"].isdigit() and int(e["name"]) not in years:
                    continue
                stack.append(int(e["entryId"]))
                continue
            rows.append({
                "entry_id": int(e["entryId"]),
                "name": e["name"],
                "folder_path": listing["path"],
                "folder_id": fid,
                "is_edoc": bool(e.get("isEdoc")),
                "extension": e.get("extension") or "",
                "entry_type": e["type"],
                "page_count": page_count(e),
                "name_date": parse_name_date(e["name"]),
                "name_meeting_type": name_meeting_type(e["name"]),
                "docview_url": docview_url(int(e["entryId"])),
            })
    return rows


def discover(refresh: bool = False, years: set[int] | None = None) -> pd.DataFrame:
    client = LaserficheClient()
    rows = walk(client, SIGNED_MINUTES_FOLDER_ID, refresh=refresh, years=years)
    df = pd.DataFrame(rows)
    df["year_folder"] = df["folder_path"].str.extract(r"Signed Minutes\\(\d{4})")[0].astype("Int64")
    df = df.sort_values(["year_folder", "name_date", "entry_id"], na_position="last")
    if years and INVENTORY_CSV.exists():
        # Partial walk: merge into the existing inventory rather than clobbering it
        old = pd.read_csv(INVENTORY_CSV)
        old = old[~old["year_folder"].isin(sorted(years))]
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(INVENTORY_CSV, index=False)
    undated = df["name_date"].isna().sum()
    print(f"Inventory: {len(df)} documents in {df['year_folder'].nunique()} year folders; "
          f"{undated} with no date in the name; {client.requests_made} portal requests.")
    return df
