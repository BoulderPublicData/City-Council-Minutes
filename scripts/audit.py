"""Write `data/audit/summary.md`: coverage, quality flags by era, and Datalab cost.

The cost section is the full-run projection the sample is meant to produce: the
observed cost per page for each step and mode in `runs.csv`, multiplied by the
pages still unprocessed in the inventory.
"""

from __future__ import annotations

import json

import pandas as pd

from scripts.config import (
    DATA_AUDIT,
    DATA_PROCESSED,
    DATALAB_RUNS_CSV,
    INVENTORY_CSV,
    MANIFEST_CSV,
    SAMPLE_CSV,
)


def _md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False, floatfmt=".2f") if len(df) else "_none_"


def cost_projection(inv: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if not DATALAB_RUNS_CSV.exists():
        return pd.DataFrame(), "_no Datalab runs yet_"
    runs = pd.read_csv(DATALAB_RUNS_CSV)
    ok = runs[runs["error"].isna() & runs["cost_cents"].notna() & (runs["page_count"] > 0)]
    # A re-run of the same (entry, step, mode) is a retry; count the latest only for rates
    latest = ok.sort_values("finished_utc").groupby(["entry_id", "step", "mode"]).tail(1)
    rate = latest.groupby(["step", "mode"]).agg(
        docs=("entry_id", "nunique"), pages=("page_count", "sum"),
        cost_usd=("cost_cents", lambda s: s.sum() / 100)).reset_index()
    rate["usd_per_1k_pages"] = rate["cost_usd"] / rate["pages"] * 1000
    total_pages = float(inv["page_count"].fillna(inv["page_count"].median()).sum())
    rate["projected_full_archive_usd"] = rate["usd_per_1k_pages"] * total_pages / 1000
    spent = runs["cost_cents"].fillna(0).sum() / 100
    conv = rate[rate["step"] == "convert"]["projected_full_archive_usd"].sum()
    lines = [f"Spent so far (all runs, including retries and tests): **${spent:,.2f}**.",
             f"Full archive: **{len(inv):,} documents, ~{total_pages:,.0f} pages** "
             "(page counts from the portal listing; missing counts filled with the median).", ""]
    for mode in rate[rate["step"] == "extract"]["mode"]:
        ext = rate[(rate["step"] == "extract") & (rate["mode"] == mode)]["projected_full_archive_usd"].sum()
        lines.append(f"- convert + **{mode}** extraction, whole archive: **≈ ${conv + ext:,.0f}**")
    return rate, "\n".join(lines)


def audit() -> None:
    inv = pd.read_csv(INVENTORY_CSV, parse_dates=["name_date"])
    out = ["# Audit summary", ""]

    # ── coverage ──
    inv["year"] = inv["name_date"].dt.year
    by_year = inv.groupby("year_folder").agg(
        documents=("entry_id", "count"), pages=("page_count", "sum"),
        imaged=("is_edoc", lambda s: int((~s.astype(bool)).sum())),
        undated_names=("name_date", lambda s: int(s.isna().sum()))).reset_index()
    out += ["## Inventory (Laserfiche `Signed Minutes`)", "",
            f"{len(inv):,} documents; {int(inv['name_date'].isna().sum())} have no parseable date "
            "in their name (listed below). *imaged* = scanned pages, PDF rendered by the portal.", "",
            _md(by_year), ""]
    undated = inv[inv["name_date"].isna()][["entry_id", "name", "folder_path"]]
    if len(undated):
        out += ["### Documents with no date in the name", "", _md(undated.head(100)), ""]
    nontypical = inv[~inv["name"].str.contains("minute", case=False, na=False)]
    if len(nontypical):
        out += ["### Documents whose name doesn't say “minutes”", "",
                "Kept in the inventory; check whether any are not council minutes.", "",
                _md(nontypical[["entry_id", "name", "folder_path"]].head(100)), ""]

    if MANIFEST_CSV.exists():
        man = pd.read_csv(MANIFEST_CSV)
        mism = man[man["pdf_pages"].notna() & man["inventory_pages"].notna() &
                   (man["pdf_pages"] != man["inventory_pages"])]
        out += ["## Downloads", "", f"{len(man)} PDFs on disk "
                f"({int((man['method'] == 'generate_pdf10').sum())} rendered from page images). "
                f"{len(mism)} have a page count different from the portal's.", ""]
        if len(mism):
            out += [_md(mism[["entry_id", "name", "pdf_pages", "inventory_pages"]]), ""]

    # ── processed tables ──
    mpath = DATA_PROCESSED / "meetings.csv"
    if mpath.exists():
        mt = pd.read_csv(mpath)
        mo = pd.read_csv(DATA_PROCESSED / "motions.csv")
        mt["era"] = (mt["meeting_date"].str[:4].astype(int) // 5 * 5).astype(str) + "s"
        mo = mo.merge(mt[["entry_id", "era"]], on="entry_id")
        era = mt.groupby("era").agg(
            meetings=("entry_id", "count"), present_mean=("n_members_present", "mean"),
            present_lt_5=("n_members_present", lambda s: int((s < 5).sum())),
            motions_mean=("n_motions", "mean"), items_mean=("n_agenda_items", "mean"),
            date_disagrees=("date_disagrees_with_name", "sum")).reset_index()
        inf = (mo.groupby(["era", "vote_inference"]).size().unstack(fill_value=0)
               .pipe(lambda d: d.div(d.sum(axis=1), axis=0)).reset_index())
        miss = mo.groupby("era").agg(
            motions=("motion_seq", "count"),
            moved_by_missing=("moved_by", lambda s: s.isna().mean()),
            seconded_missing=("seconded_by", lambda s: s.isna().mean()),
            vote_text_missing=("vote_text", lambda s: s.isna().mean())).reset_index()
        out += ["## Extracted meetings by era", "",
                "`present_lt_5` counts meetings where fewer than five members were found present "
                "— almost always a missed roll call, since council needs five for a quorum. "
                "More than nine present happens at post-election transition meetings.", "",
                _md(era), "", "### How each motion's per-member votes were obtained (share of motions)", "",
                _md(inf), "", "### Missing motion fields (share of motions)", "", _md(miss), ""]
        flagged = mt[(mt["n_members_present"] < 5) | (mt["n_members_present"] > 9)
                     | mt["date_disagrees_with_name"]]
        if len(flagged):
            out += ["### Meetings to check by hand", "",
                    _md(flagged[["entry_id", "meeting_date", "document_name", "n_members_present",
                                 "date_disagrees_with_name"]]), ""]

    xpath = DATA_PROCESSED / "excluded_roll_call.csv"
    if xpath.exists():
        ex = pd.read_csv(xpath)
        out += ["## Names dropped from the roll call", "",
                f"{len(ex)} names the extractor listed as council members were dropped by "
                "`tidy.non_members` (public speakers who didn't show, other boards' members). "
                "Check that none is a real council member.", "",
                _md(ex[["entry_id", "meeting_date", "name_as_printed", "status", "note", "reason"]]), ""]

    # ── cost ──
    rate, text = cost_projection(inv)
    out += ["## Datalab cost and full-run projection", "", text, "", _md(rate), ""]
    if SAMPLE_CSV.exists():
        s = pd.read_csv(SAMPLE_CSV)
        out += [f"Sample: {len(s)} meetings, {int(s['page_count'].fillna(0).sum())} pages, "
                f"{int(s['in_gold'].sum())} with a hand-transcribed reference.", ""]
    (DATA_AUDIT / "summary.md").write_text("\n".join(out) + "\n")
    (DATA_AUDIT / "cost.json").write_text(json.dumps(rate.to_dict("records"), indent=1, default=str))
    print(f"audit: wrote {DATA_AUDIT / 'summary.md'}")
