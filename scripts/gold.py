"""Load the hand-transcribed meetings (2021-05 → 2022-12) as a reference set.

`minutes.json` at the repo root was typed by volunteers in an HJSON editor and
contains trailing commas, so it is not strict JSON. `load_gold()` repairs that,
attaches each record's Laserfiche entry id (from `minutes_url`), and splits the
occasional comma-joined name list. `write_gold()` saves the repaired copy to
`data/lookups/gold/` so scoring never depends on the lenient parse.

The hand transcription is a *reference*, not ground truth: some records have
obvious slips (e.g. the 2022-09-14 record lists the 2021 council). The scoring
report shows disagreements side by side so they can be adjudicated.
"""

from __future__ import annotations

import json
import re
from typing import Any

from scripts.config import GOLD_JSON, INVENTORY_CSV, ROOT


def _split_names(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values or []:
        for part in re.split(r"[,;]| and ", v or ""):
            part = part.strip().strip(".")
            if part:
                out.append(part)
    return out


def load_gold() -> list[dict[str, Any]]:
    if GOLD_JSON.exists():
        return json.loads(GOLD_JSON.read_text())
    raw = (ROOT / "minutes.json").read_text()
    records = json.loads(re.sub(r",(\s*[\]}])", r"\1", raw))
    for r in records:
        m = re.search(r"(?:[?&]id=|/edoc/)(\d+)", r.get("minutes_url", ""))
        r["entry_id"] = int(m.group(1)) if m else None
        r["attendees"] = _split_names(r.get("attendees", []))
        ca = r.get("consent_agenda") or {}
        for k in ("yeas", "nays", "absent"):
            ca[k] = _split_names(ca.get(k, []))
        for h in r.get("public_hearings") or []:
            for k in ("yeas", "nays", "absent"):
                h[k] = _split_names(h.get(k, []))
    return records


def resolve_by_date(records: list[dict[str, Any]]) -> None:
    """Two records link to a folder (Browse.aspx?id=…) rather than the document; when an
    entry id isn't a document in the inventory, use the one document with that date."""
    if not INVENTORY_CSV.exists():
        return
    import pandas as pd

    inv = pd.read_csv(INVENTORY_CSV)
    ids = set(inv["entry_id"])
    for r in records:
        if r.get("entry_id") in ids:
            continue
        same_day = inv[inv["name_date"] == r.get("date")]
        if len(same_day) == 1:
            r["linked_entry_id"] = r["entry_id"]
            r["entry_id"] = int(same_day["entry_id"].iloc[0])


def gold_entry_ids() -> list[int]:
    return [g["entry_id"] for g in load_gold() if g.get("entry_id")]


def write_gold() -> None:
    GOLD_JSON.parent.mkdir(parents=True, exist_ok=True)
    if GOLD_JSON.exists():
        GOLD_JSON.unlink()
    records = load_gold()
    resolve_by_date(records)
    GOLD_JSON.write_text(json.dumps(records, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    write_gold()
