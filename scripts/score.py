"""Score extractions against the hand-transcribed 2021–22 meetings, per extraction mode.

For every mode that has extractions, the tables are rebuilt into
`data/interim/tidy/<mode>/` and compared with `data/lookups/gold/` on the fields
the hand transcription covers:

* attendance — present members (set precision / recall / exact match)
* consent agenda — item count; yea and nay sets
* public hearings — count; for hearings matched by title, mover, seconder, yea/nay sets
* open comment — speaker-name recall

Disagreements are listed meeting by meeting in `data/audit/accuracy.md`, because
the reference has its own slips and some "errors" will turn out to be the
reference's. A second section compares modes with each other on *every* sampled
meeting (not just the reference ones), which is the only accuracy signal for the
years before 2021.
"""

from __future__ import annotations

import difflib
import json
import re
from typing import Any

import pandas as pd

from scripts.config import DATA_AUDIT, DATA_INTERIM, DATA_LOOKUPS, DATALAB_EXTRACT, SAMPLE_CSV
from scripts.gold import load_gold
from scripts.names import member_key, snap
from scripts.tidy import tidy_all

_PLACEHOLDERS = {"none", "n/a", "na", "absent", "late", "-", ""}


def _keys(names: list[str] | None, roster: list[str] | None = None,
          everyone: list[str] | None = None) -> set[str]:
    """Reference names → member keys. The hand transcription has typos ("Walllach",
    "Folerts"), placeholders ("None", "Late", "Absent") and shorthand ("All"); snap
    names to the meeting's roll call and expand "All" to everyone present."""
    out: set[str] = set()
    for n in names or []:
        token = str(n).strip().strip(".").lower()
        if token in _PLACEHOLDERS:
            continue
        if token == "all":
            out |= set(everyone or [])
            continue
        k = member_key(n)
        if k:
            out.add(snap(k, roster or [], cutoff=0.75))
    return out


def _prf(pred: set[str], ref: set[str]) -> tuple[float | None, float | None]:
    if not pred and not ref:
        return 1.0, 1.0
    p = len(pred & ref) / len(pred) if pred else None
    r = len(pred & ref) / len(ref) if ref else None
    return p, r


def _norm(s: str | list[str] | None) -> str:
    if isinstance(s, list):  # a few hand-typed hearing names are lists of lines
        s = " ".join(str(x) for x in s)
    return " ".join(s.lower().split()) if isinstance(s, str) else ""


def _numbers(s: str | list[str] | None) -> set[str]:
    return set(re.findall(r"(?<!\d)\d{3,4}(?!\d)", _norm(s)))


def _match_hearing(name: str | list[str], cands: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Match a reference hearing to an extracted one: by ordinance/resolution number when
    the reference names one ("Ordinance 8500"), else by title similarity."""
    nums = _numbers(name)
    if nums:
        hits = [c for c in cands if nums & (_numbers(c.get("name")) | _numbers(c.get("description")))]
        if hits:
            return hits[0]
    best, score = None, 0.0
    for c in cands:
        r = difflib.SequenceMatcher(None, _norm(name), _norm(c.get("name"))).ratio()
        if r > score:
            best, score = c, r
    return best if score >= 0.5 else None


def score_mode(mode: str) -> tuple[pd.DataFrame, list[str]]:
    out_dir = DATA_INTERIM / "tidy" / mode
    tidy_all(mode=mode, out_dir=out_dir)
    nested = {m["entry_id"]: m for m in json.loads((out_dir / "meetings.json").read_text())}
    rows, notes = [], []
    for g in load_gold():
        eid = g.get("entry_id")
        if eid not in nested:
            continue
        if nested[eid]["date"] != g["date"]:
            notes.append(f"- `{eid}` date: ref={g['date']} | ext={nested[eid]['date']}")
        p = nested[eid]
        roster = p["attendees"] + p["absent"]

        def ref(names: list[str] | None, p: dict[str, Any] = p, roster: list[str] = roster) -> set[str]:
            return _keys(names, roster, p["attendees"])

        ref_att = ref(g["attendees"])
        att_p, att_r = _prf(set(p["attendees"]), ref_att)
        gc, pc = g.get("consent_agenda") or {}, p["consent_agenda"]
        row = {
            "entry_id": eid, "date": g["date"], "date_match": p["date"] == g["date"],
            "attendance_precision": att_p, "attendance_recall": att_r,
            "attendance_exact": set(p["attendees"]) == ref_att,
            "consent_items_ref": len(gc.get("items") or []), "consent_items_ext": len(pc["items"]),
            "consent_yeas_exact": set(pc["yeas"]) == ref(gc.get("yeas")),
            "consent_nays_exact": set(pc["nays"]) == ref(gc.get("nays")),
            "hearings_ref": len(g.get("public_hearings") or []),
            "hearings_ext": len(p["public_hearings"]),
        }
        h_fields = {"mover": [], "seconder": [], "yeas": [], "nays": []}
        for gh in g.get("public_hearings") or []:
            ph = _match_hearing(gh.get("name", ""), p["public_hearings"])
            if not ph:
                notes.append(f"- `{eid}` {g['date']}: reference hearing not found: "
                             f"“{_norm(gh.get('name'))[:90]}”")
                continue
            ry, rn = ref(gh.get("yeas")), ref(gh.get("nays"))
            h_fields["mover"].append(min(ref([gh.get("motion") or ""]) or {None}) == ph["motion"])
            h_fields["seconder"].append(min(ref([gh.get("seconded") or ""]) or {None}) == ph["seconded"])
            h_fields["yeas"].append(ry == set(ph["yeas"]))
            h_fields["nays"].append(rn == set(ph["nays"]))
            if ry != set(ph["yeas"]) or rn != set(ph["nays"]):
                notes.append(f"- `{eid}` {g['date']} hearing “{_norm(gh.get('name'))[:60]}”: "
                             f"ref yeas={sorted(ry)} nays={sorted(rn)}"
                             f" | ext yeas={sorted(ph['yeas'])} nays={sorted(ph['nays'])}")
        for k, v in h_fields.items():
            row[f"hearing_{k}_match_rate"] = sum(v) / len(v) if v else None
        ref_oc = {_norm(s.get("name")) for s in g.get("open_comment") or [] if s.get("name")}
        ext_oc = {_norm(s["name"]) for s in p["open_comment"]}
        row["open_comment_ref"] = len(ref_oc)
        row["open_comment_recall"] = (sum(1 for n in ref_oc if difflib.get_close_matches(n, ext_oc, 1, 0.8))
                                      / len(ref_oc)) if ref_oc else None
        if not row["attendance_exact"]:
            notes.append(f"- `{eid}` {g['date']} attendance: ref={sorted(ref_att)} "
                         f"| ext={sorted(p['attendees'])}")
        if not (row["consent_yeas_exact"] and row["consent_nays_exact"]):
            notes.append(f"- `{eid}` {g['date']} consent vote: ref yeas={sorted(ref(gc.get('yeas')))} "
                         f"nays={sorted(ref(gc.get('nays')))} | ext yeas={sorted(pc['yeas'])} "
                         f"nays={sorted(pc['nays'])}")
        rows.append(row)
    return pd.DataFrame(rows), notes


def compare_modes(a: str, b: str) -> pd.DataFrame:
    """Agreement between two modes' tables on every meeting both extracted."""
    ta = {n: pd.read_csv(DATA_INTERIM / "tidy" / a / f"{n}.csv") for n in ("meetings", "attendance", "motions")}
    tb = {n: pd.read_csv(DATA_INTERIM / "tidy" / b / f"{n}.csv") for n in ("meetings", "attendance", "motions")}
    common = sorted(set(ta["meetings"]["entry_id"]) & set(tb["meetings"]["entry_id"]))
    rows = []
    for eid in common:
        def present(t: dict[str, pd.DataFrame], eid: int = eid) -> set[str]:
            at = t["attendance"]
            return set(at[(at["entry_id"] == eid) & (at["status"] == "present")]["member"])
        ma = ta["motions"][ta["motions"]["entry_id"] == eid]
        mb = tb["motions"][tb["motions"]["entry_id"] == eid]
        date = ta["meetings"].set_index("entry_id").loc[eid, "meeting_date"]
        rows.append({"entry_id": eid, "meeting_date": date, "year": int(str(date)[:4]),
                     "attendance_agree": present(ta) == present(tb),
                     f"motions_{a}": len(ma), f"motions_{b}": len(mb),
                     f"recorded_votes_{a}": int((ma["vote_inference"] != "no_vote_recorded").sum()),
                     f"recorded_votes_{b}": int((mb["vote_inference"] != "no_vote_recorded").sum())})
    return pd.DataFrame(rows)


def _fmt(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False, floatfmt=".2f") if len(df) else "_none_"


def score() -> None:
    modes = sorted(p.name for p in DATALAB_EXTRACT.glob("*") if p.is_dir() and any(p.glob("*/*.json")))
    lines = ["# Extraction accuracy (quarterly sample)", "",
             "Reference: the 41 hand-transcribed meetings (2021-05 → 2022-12) in `minutes.json`. "
             "The reference is volunteer-typed and has its own errors; read disagreements before "
             "counting them against the extractor.", ""]
    summary = []
    detail: dict[str, list[str]] = {}
    for mode in modes:
        df, notes = score_mode(mode)
        detail[mode] = notes
        if df.empty:
            continue
        summary.append({
            "mode": mode, "meetings_scored": len(df), "date_match": df["date_match"].mean(),
            "attendance_exact": df["attendance_exact"].mean(),
            "attendance_recall": df["attendance_recall"].mean(),
            "consent_yeas_exact": df["consent_yeas_exact"].mean(),
            "consent_nays_exact": df["consent_nays_exact"].mean(),
            "hearing_count_match": (df["hearings_ref"] == df["hearings_ext"]).mean(),
            "hearing_mover_match": df["hearing_mover_match_rate"].mean(),
            "hearing_yeas_match": df["hearing_yeas_match_rate"].mean(),
            "hearing_nays_match": df["hearing_nays_match_rate"].mean(),
            "open_comment_recall": df["open_comment_recall"].mean(),
        })
        df.to_csv(DATA_AUDIT / f"accuracy_{mode}.csv", index=False)
    lines += ["## Summary against the reference", "", _fmt(pd.DataFrame(summary)), ""]
    if {"fast", "balanced"} <= set(modes):
        cmp = compare_modes("balanced", "fast")
        cmp.to_csv(DATA_AUDIT / "mode_agreement.csv", index=False)
        cmp["era"] = (cmp["year"] // 5 * 5).astype(str) + "s"
        by_era = cmp.groupby("era").agg(
            meetings=("entry_id", "count"), attendance_agree=("attendance_agree", "mean"),
            motions_balanced=("motions_balanced", "mean"), motions_fast=("motions_fast", "mean"),
            recorded_votes_balanced=("recorded_votes_balanced", "mean"),
            recorded_votes_fast=("recorded_votes_fast", "mean")).reset_index()
        lines += ["## Balanced vs. fast on every sampled meeting, by 5-year era", "",
                  "No reference exists before 2021, so agreement between the two modes is the "
                  "signal there. Fewer motions in one mode almost always means it missed some.", "",
                  _fmt(by_era), ""]
    adj_path = DATA_LOOKUPS / "adjudications.csv"
    if adj_path.exists():
        adj = pd.read_csv(adj_path)
        lines += ["## Disagreements checked against the minutes", "",
                  "Each row was read in the OCR'd minutes by hand "
                  "(`data/lookups/adjudications.csv`). `reference_error` means the extraction "
                  "matches the minutes and the hand transcription does not.", "",
                  _fmt(adj.groupby(["field", "verdict"]).size().rename("n").reset_index()), "",
                  _fmt(adj), ""]
    for mode, notes in detail.items():
        lines += [f"## Disagreements to adjudicate — {mode}", ""] + (notes or ["_none_"]) + [""]
    if SAMPLE_CSV.exists():
        lines += [f"Sample definition: `{SAMPLE_CSV.relative_to(SAMPLE_CSV.parents[2])}`."]
    (DATA_AUDIT / "accuracy.md").write_text("\n".join(lines) + "\n")
    print(f"score: wrote {DATA_AUDIT / 'accuracy.md'}")
    if summary:
        print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    score()
