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
from typing import Any

import pandas as pd

from scripts.config import DATA_AUDIT, DATA_INTERIM, DATALAB_EXTRACT, SAMPLE_CSV
from scripts.gold import load_gold
from scripts.names import member_key
from scripts.tidy import tidy_all


def _keys(names: list[str]) -> set[str]:
    return {k for k in (member_key(n) for n in names or []) if k}


def _prf(pred: set[str], ref: set[str]) -> tuple[float | None, float | None]:
    if not pred and not ref:
        return 1.0, 1.0
    p = len(pred & ref) / len(pred) if pred else None
    r = len(pred & ref) / len(ref) if ref else None
    return p, r


def _norm(s: str | None) -> str:
    return " ".join((s or "").lower().split())


def _match_hearing(name: str, cands: list[dict[str, Any]]) -> dict[str, Any] | None:
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
        p = nested[eid]
        att_p, att_r = _prf(set(p["attendees"]), _keys(g["attendees"]))
        gc, pc = g.get("consent_agenda") or {}, p["consent_agenda"]
        row = {
            "entry_id": eid, "date": g["date"], "date_match": p["date"] == g["date"],
            "attendance_precision": att_p, "attendance_recall": att_r,
            "attendance_exact": set(p["attendees"]) == _keys(g["attendees"]),
            "consent_items_ref": len(gc.get("items") or []), "consent_items_ext": len(pc["items"]),
            "consent_yeas_exact": set(pc["yeas"]) == _keys(gc.get("yeas")),
            "consent_nays_exact": set(pc["nays"]) == _keys(gc.get("nays")),
            "hearings_ref": len(g.get("public_hearings") or []),
            "hearings_ext": len(p["public_hearings"]),
        }
        h_fields = {"mover": [], "seconder": [], "yeas": [], "nays": []}
        for gh in g.get("public_hearings") or []:
            ph = _match_hearing(gh.get("name", ""), p["public_hearings"])
            if not ph:
                notes.append(f"- `{eid}` {g['date']}: reference hearing not found: "
                             f"“{(gh.get('name') or '')[:90]}”")
                continue
            h_fields["mover"].append(member_key(gh.get("motion")) == ph["motion"])
            h_fields["seconder"].append(member_key(gh.get("seconded")) == ph["seconded"])
            h_fields["yeas"].append(_keys(gh.get("yeas")) == set(ph["yeas"]))
            h_fields["nays"].append(_keys(gh.get("nays")) == set(ph["nays"]))
            if _keys(gh.get("yeas")) != set(ph["yeas"]) or _keys(gh.get("nays")) != set(ph["nays"]):
                notes.append(f"- `{eid}` {g['date']} hearing “{(gh.get('name') or '')[:60]}”: "
                             f"ref yeas={sorted(_keys(gh.get('yeas')))} nays={sorted(_keys(gh.get('nays')))}"
                             f" | ext yeas={sorted(ph['yeas'])} nays={sorted(ph['nays'])}")
        for k, v in h_fields.items():
            row[f"hearing_{k}_match_rate"] = sum(v) / len(v) if v else None
        ref_oc = {_norm(s.get("name")) for s in g.get("open_comment") or [] if s.get("name")}
        ext_oc = {_norm(s["name"]) for s in p["open_comment"]}
        row["open_comment_ref"] = len(ref_oc)
        row["open_comment_recall"] = (sum(1 for n in ref_oc if difflib.get_close_matches(n, ext_oc, 1, 0.8))
                                      / len(ref_oc)) if ref_oc else None
        if not row["attendance_exact"]:
            notes.append(f"- `{eid}` {g['date']} attendance: ref={sorted(_keys(g['attendees']))} "
                         f"| ext={sorted(p['attendees'])}")
        if not (row["consent_yeas_exact"] and row["consent_nays_exact"]):
            notes.append(f"- `{eid}` {g['date']} consent vote: ref yeas={sorted(_keys(gc.get('yeas')))} "
                         f"nays={sorted(_keys(gc.get('nays')))} | ext yeas={pc['yeas']} nays={pc['nays']}")
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
