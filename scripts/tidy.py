"""Turn Datalab extractions into the six canonical tables plus a nested JSON export.

Reads `data/interim/datalab/extract/<mode>/<year>/<entry_id>.json`, writes
`data/processed/{meetings,attendance,agenda_items,speakers,motions,member_votes}.csv`,
`data/processed/meetings.json` (the README's per-meeting format, extended), and
`data/processed/provenance.csv`.

**Vote inference.** Many minutes state only a tally and the dissenters ("The
motion carried 6:3, Havlick, Morzel and Riggle opposed"). `infer_votes` fills in
the unnamed members from that meeting's own roll call as `yes`, and roll-call
absentees as `absent`, flagging every such row `vote_source = inferred`. It
refuses to infer when the result would contradict a stated count (e.g. a member
left early and the minutes say 7:1 with eight present) or when the minutes list
the yes votes explicitly but omit some present members; those motions are
labeled `inconsistent_not_inferred` / `partial_stated_only` and keep only the
stated rows.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from scripts import schema
from scripts.config import (
    DATA_PROCESSED,
    DATALAB_EXTRACT,
    DATALAB_MARKDOWN,
    INVENTORY_CSV,
    MANIFEST_CSV,
    PROVENANCE_CSV,
)
from scripts.extraction_schema import ACTION_TYPES, MEETING_TYPES, MOTION_RESULTS
from scripts.names import member_key, normalize_list, snap

log = logging.getLogger(__name__)


def strip_meta(o: Any) -> Any:
    """Drop Datalab's `<field>_citations` / `<field>_meta` siblings."""
    if isinstance(o, dict):
        return {k: strip_meta(v) for k, v in o.items()
                if not (k.endswith("_citations") or k.endswith("_meta"))}
    if isinstance(o, list):
        return [strip_meta(i) for i in o]
    return o


def item_key(number: str | None) -> str | None:
    """'5.A.' / '5 a' / '5(a)' → '5A' so motions can be joined to agenda items."""
    if not number:
        return None
    k = re.sub(r"[^0-9A-Za-z]", "", str(number)).upper()
    return k or None


def _clean(v: Any) -> Any:
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def _join(values: list[str] | None) -> str | None:
    vals = [str(v).strip() for v in values or [] if str(v).strip()]
    return "; ".join(vals) if vals else None


def _int(v: Any) -> int | None:
    try:
        return int(v) if v is not None and str(v).strip() != "" else None
    except (TypeError, ValueError):
        return None


# ── vote inference ──────────────────────────────────────────────────────────

def infer_votes(present: list[str], absent: list[str], motion: dict[str, Any]
                ) -> tuple[list[tuple[str, str, str]], str]:
    """Return ([(member, vote, vote_source)], vote_inference_label) for one motion."""
    roster = present + [a for a in absent if a not in present]
    yes = normalize_list(motion.get("yes_votes"), roster)
    no = normalize_list(motion.get("no_votes"), roster)
    abstain = normalize_list(motion.get("abstained"), roster)
    out = normalize_list(motion.get("absent_or_not_voting"), roster)

    rows: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for names, vote in ((no, "no"), (abstain, "abstain"), (out, "absent"), (yes, "yes")):
        for m in names:
            if m not in seen:
                rows.append((m, vote, "stated"))
                seen.add(m)

    yes_count, no_count = _int(motion.get("yes_count")), _int(motion.get("no_count"))
    unanimous = bool(motion.get("stated_unanimous"))
    has_vote = bool(_clean(motion.get("vote_text"))) or yes_count is not None \
        or no_count is not None or unanimous or bool(rows)
    if motion.get("result") == "no_vote_recorded" and not rows and yes_count is None:
        has_vote = False
    if not has_vote:
        return rows, "no_vote_recorded"

    remaining = [m for m in present if m not in seen]
    roll_absent = [a for a in absent if a not in seen and a not in present]
    if not remaining:
        rows += [(a, "absent", "inferred") for a in roll_absent]
        return rows, "complete_as_stated"
    if yes:
        # The minutes listed yes votes but left some present members out: they may
        # have left the dais. Don't guess.
        return rows, "partial_stated_only"
    n_no = sum(1 for _, v, _ in rows if v == "no")
    consistent = (yes_count is None or yes_count == len(remaining)) and \
                 (no_count is None or no_count == n_no) and not (unanimous and n_no)
    if not consistent:
        return rows, "inconsistent_not_inferred"
    rows += [(m, "yes", "inferred") for m in remaining]
    rows += [(a, "absent", "inferred") for a in roll_absent]
    return rows, "inferred_from_roll_call"


# ── per-document tidy ───────────────────────────────────────────────────────

def tidy_one(entry: dict[str, Any], doc: dict[str, Any], extraction_mode: str,
             schema_version: str) -> dict[str, list[dict[str, Any]]]:
    x = strip_meta(doc)
    eid = int(entry["entry_id"])

    present_raw = [p for p in x.get("members_present") or [] if isinstance(p, dict)]
    absent_raw = [p for p in x.get("members_absent") or [] if isinstance(p, dict)]
    present = [k for k in (member_key(p.get("name")) for p in present_raw) if k]
    absent = [k for k in (member_key(p.get("name")) for p in absent_raw) if k]
    roster = list(dict.fromkeys(present + absent))

    name_date = entry.get("name_date") if isinstance(entry.get("name_date"), str) else None
    ext_date = _clean(x.get("meeting_date"))
    if ext_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", ext_date):
        ext_date = None
    meeting_date = ext_date or name_date
    mtype = x.get("meeting_type") if x.get("meeting_type") in MEETING_TYPES else None
    mtype = mtype or entry.get("name_meeting_type") or "regular"
    if isinstance(mtype, float):
        mtype = "regular"

    attendance: list[dict[str, Any]] = []
    seen_att: set[str] = set()
    for status, raws in (("present", present_raw), ("absent", absent_raw)):
        for p in raws:
            k = member_key(p.get("name"))
            if not k or k in seen_att:
                continue
            seen_att.add(k)
            attendance.append({"entry_id": eid, "meeting_date": meeting_date, "member": k,
                               "name_as_printed": str(p.get("name")).strip(),
                               "title": _clean(p.get("title")), "status": status,
                               "note": _clean(p.get("attendance_note") or p.get("note"))})

    items, speakers = [], []
    for seq, it in enumerate(x.get("agenda_items") or [], 1):
        if not isinstance(it, dict):
            continue
        hs = [h for h in it.get("hearing_speakers") or [] if isinstance(h, dict) and _clean(h.get("name"))]
        items.append({
            "entry_id": eid, "item_seq": seq, "item_number": _clean(it.get("item_number")),
            "item_key": item_key(it.get("item_number")), "section": _clean(it.get("section")),
            "title": _clean(it.get("title")),
            "ordinance_or_resolution_numbers": _join(it.get("ordinance_or_resolution_numbers")),
            "is_public_hearing": bool(it.get("is_public_hearing")),
            "hearing_opened_time": _clean(it.get("hearing_opened_time")),
            "hearing_closed_time": _clean(it.get("hearing_closed_time")),
            "n_hearing_speakers": len(hs), "outcome_summary": _clean(it.get("outcome_summary")),
        })
        for i, h in enumerate(hs, 1):
            speakers.append({"entry_id": eid, "context": "public_hearing",
                             "item_number": _clean(it.get("item_number")), "speaker_seq": i,
                             "name": h["name"].strip(), "topic": None,
                             "position": _clean(h.get("position"))})
    for i, s in enumerate(x.get("open_comment_speakers") or [], 1):
        if isinstance(s, dict) and _clean(s.get("name")):
            speakers.append({"entry_id": eid, "context": "open_comment", "item_number": None,
                             "speaker_seq": i, "name": s["name"].strip(),
                             "topic": _clean(s.get("topic")), "position": None})

    motions, votes = [], []
    for seq, m in enumerate(x.get("motions") or [], 1):
        if not isinstance(m, dict):
            continue
        rows, label = infer_votes(present, absent, m)
        counts = {v: sum(1 for _, vv, _ in rows if vv == v) for v in schema.VOTES}
        motions.append({
            "entry_id": eid, "motion_seq": seq,
            "agenda_item_number": _clean(m.get("agenda_item_number")),
            "item_key": item_key(m.get("agenda_item_number")),
            "motion_text": _clean(m.get("motion_text")),
            "action_type": m.get("action_type") if m.get("action_type") in ACTION_TYPES else "other",
            "ordinance_or_resolution_numbers": _join(m.get("ordinance_or_resolution_numbers")),
            "moved_by": snap(member_key(m.get("moved_by")), roster),
            "seconded_by": snap(member_key(m.get("seconded_by")), roster),
            "vote_text": _clean(m.get("vote_text")),
            "result": m.get("result") if m.get("result") in MOTION_RESULTS else "no_vote_recorded",
            "yes_count": _int(m.get("yes_count")), "no_count": _int(m.get("no_count")),
            "stated_unanimous": bool(m.get("stated_unanimous")), "vote_inference": label,
            "n_yes": counts["yes"], "n_no": counts["no"], "n_abstain": counts["abstain"],
            "n_absent": counts["absent"],
        })
        votes += [{"entry_id": eid, "motion_seq": seq, "member": mem, "vote": v, "vote_source": src}
                  for mem, v, src in rows]

    meeting = {
        "entry_id": eid, "meeting_date": meeting_date,
        "date_source": "extracted" if ext_date else "document_name",
        "date_disagrees_with_name": bool(ext_date and name_date and ext_date != name_date),
        "meeting_type": mtype, "meeting_title": _clean(x.get("meeting_title")),
        "document_name": entry["name"], "location": _clean(x.get("location")),
        "called_to_order_time": _clean(x.get("called_to_order_time")),
        "adjourned_time": _clean(x.get("adjourned_time")),
        "presiding_officer": _clean(x.get("presiding_officer")),
        "n_members_present": sum(a["status"] == "present" for a in attendance),
        "n_members_absent": sum(a["status"] == "absent" for a in attendance),
        "n_agenda_items": len(items), "n_motions": len(motions),
        "page_count": entry.get("page_count"), "source_url": entry["docview_url"],
        "extraction_mode": extraction_mode, "schema_version": schema_version,
        "_call_ups": [c for c in x.get("call_up_items") or [] if isinstance(c, str)],
    }
    return {"meetings": [meeting], "attendance": attendance, "agenda_items": items,
            "speakers": speakers, "motions": motions, "member_votes": votes}


# ── nested export (README format, extended) ─────────────────────────────────

def nested_meeting(t: dict[str, pd.DataFrame], eid: int) -> dict[str, Any]:
    def sub(name: str) -> pd.DataFrame:
        df = t[name]
        return df[df["entry_id"] == eid]

    mt = sub("meetings").iloc[0]
    att, items, mots, votes, spk = (sub("attendance"), sub("agenda_items"), sub("motions"),
                                    sub("member_votes"), sub("speakers"))

    def vote_lists(seq: int) -> dict[str, list[str]]:
        v = votes[votes["motion_seq"] == seq]
        return {"yeas": v[v["vote"] == "yes"]["member"].tolist(),
                "nays": v[v["vote"] == "no"]["member"].tolist(),
                "absent": v[v["vote"].isin(["absent", "abstain"])]["member"].tolist()}

    consent_items = items[items["section"].fillna("").str.contains("consent", case=False)]
    consent_motion = mots[mots["action_type"] == "consent_agenda"]
    consent = {"items": consent_items["title"].dropna().tolist(), "yeas": [], "nays": [], "absent": []}
    if len(consent_motion):
        consent.update(vote_lists(int(consent_motion.iloc[0]["motion_seq"])))

    hearings = []
    for it in items[items["is_public_hearing"]].itertuples():
        hm = mots[(mots["item_key"] == it.item_key) & (mots["action_type"] != "amendment")]
        h = {"name": it.title, "description": it.outcome_summary,
             "opened": it.hearing_opened_time, "closed": it.hearing_closed_time,
             "speakers": spk[(spk["context"] == "public_hearing") &
                             (spk["item_number"] == it.item_number)]["name"].tolist(),
             "motion": None, "seconded": None, "yeas": [], "nays": [], "absent": []}
        if len(hm):
            last = hm.iloc[-1]
            h.update({"motion": last["moved_by"], "seconded": last["seconded_by"]},
                     **vote_lists(int(last["motion_seq"])))
        hearings.append(h)

    oc = spk[spk["context"] == "open_comment"]
    return {
        "date": mt["meeting_date"], "minutes_url": mt["source_url"], "entry_id": int(eid),
        "meeting_type": mt["meeting_type"],
        "attendees": att[att["status"] == "present"]["member"].tolist(),
        "absent": att[att["status"] == "absent"]["member"].tolist(),
        "open_comment": [{"name": r.name, "topic": r.topic} for r in oc.itertuples()],
        "consent_agenda": consent,
        "callup_checkin": mt["_call_ups"],
        "public_hearings": hearings,
        "motions": [{**{k: (None if pd.isna(v) else v) for k, v in m.items()
                        if k not in ("entry_id",)}, **vote_lists(int(m["motion_seq"]))}
                    for m in mots.to_dict("records")],
    }


# ── driver ──────────────────────────────────────────────────────────────────

def _extract_files(mode: str) -> list[Path]:
    return sorted((DATALAB_EXTRACT / mode).glob("*/*.json"))


def tidy_all(mode: str = "balanced", out_dir: Path = DATA_PROCESSED) -> dict[str, pd.DataFrame]:
    inv = pd.read_csv(INVENTORY_CSV).set_index("entry_id")
    acc: dict[str, list[dict[str, Any]]] = {k: [] for k in schema.TABLES}
    prov = []
    man = pd.read_csv(MANIFEST_CSV).set_index("entry_id") if MANIFEST_CSV.exists() else None
    for path in _extract_files(mode):
        rec = json.loads(path.read_text())
        eid = int(rec["entry_id"])
        if eid not in inv.index:
            log.warning("entry %s not in inventory; skipping", eid)
            continue
        entry = {"entry_id": eid, **inv.loc[eid].to_dict()}
        part = tidy_one(entry, rec["extraction"], rec.get("extraction_mode", mode),
                        rec.get("schema_version", ""))
        for k, rows in part.items():
            acc[k].extend(rows)
        conv = DATALAB_MARKDOWN / path.parent.name / f"{eid}.convert.json"
        cmeta = json.loads(conv.read_text()) if conv.exists() else {}
        m = man.loc[eid] if man is not None and eid in man.index else None
        prov.append({
            "entry_id": eid, "source_url": entry["docview_url"],
            "pdf_path": None if m is None else f"data/original/laserfiche/{m['local_path']}",
            "fetch_method": None if m is None else m["method"],
            "pdf_sha256": None if m is None else m["sha256"],
            "fetched_utc": None if m is None else m["fetched_utc"],
            "convert_request_id": cmeta.get("_request_id"), "convert_mode": cmeta.get("mode"),
            "parse_quality_score": cmeta.get("parse_quality_score"),
            "extract_request_id": rec.get("request_id"), "extraction_mode": rec.get("extraction_mode"),
            "schema_version": rec.get("schema_version"),
        })

    tables: dict[str, pd.DataFrame] = {}
    for name, sch in schema.TABLES.items():
        df = pd.DataFrame(acc[name], columns=list(sch.columns) + (["_call_ups"] if name == "meetings" else []))
        for col, c in sch.columns.items():
            if str(c.dtype) == "Int64":
                df[col] = df[col].astype("Int64")
            elif str(c.dtype) == "bool":
                df[col] = df[col].astype(bool)
            elif str(c.dtype) in ("int64", "int"):
                df[col] = df[col].astype("int64")
            elif str(c.dtype) == "float64":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
        tables[name] = df
    for name, sch in schema.TABLES.items():
        sch.validate(tables[name].drop(columns=["_call_ups"], errors="ignore"))

    out_dir.mkdir(parents=True, exist_ok=True)
    nested = [nested_meeting(tables, eid) for eid in
              tables["meetings"].sort_values("meeting_date", ascending=False)["entry_id"]]
    (out_dir / "meetings.json").write_text(json.dumps(nested, indent=1, ensure_ascii=False, default=str))
    tables["meetings"] = tables["meetings"].drop(columns=["_call_ups"])
    for name, df in tables.items():
        sort = [c for c in ("entry_id", "item_seq", "motion_seq", "speaker_seq", "member") if c in df]
        df.sort_values(sort).to_csv(out_dir / f"{name}.csv", index=False)
    pd.DataFrame(prov).to_csv(out_dir / "provenance.csv" if out_dir != DATA_PROCESSED
                              else PROVENANCE_CSV, index=False)
    print("tidy: " + ", ".join(f"{k}={len(v)}" for k, v in tables.items()))
    return tables
