"""Choose one meeting per (year, quarter) to test the pipeline before the full run.

Within each quarter the pick is random but reproducible (seeded per quarter, so
adding a newly filed meeting in one quarter never reshuffles the others). For
quarters that overlap the hand-transcribed reference set (2021-05 → 2022-12) the
pick is drawn from the reference meetings, so the sample can be scored.

The quarter comes from the date in the document name; documents whose names
carry no parseable date are listed in the audit rather than guessed at.
"""

from __future__ import annotations

import random

import pandas as pd

from scripts.config import INVENTORY_CSV, SAMPLE_CSV
from scripts.gold import load_gold

FIRST_YEAR = 2000


def build_sample(seed: int = 20261025) -> pd.DataFrame:
    inv = pd.read_csv(INVENTORY_CSV, parse_dates=["name_date"])
    inv = inv[inv["name_date"].notna() & (inv["name_date"].dt.year >= FIRST_YEAR)].copy()
    inv["year"] = inv["name_date"].dt.year
    inv["quarter"] = inv["name_date"].dt.quarter
    gold_ids = {g["entry_id"] for g in load_gold() if g.get("entry_id")}
    inv["in_gold"] = inv["entry_id"].isin(gold_ids)

    picks = []
    for (year, q), grp in inv.groupby(["year", "quarter"]):
        pool = grp[grp["in_gold"]] if grp["in_gold"].any() else grp
        rng = random.Random(f"{seed}-{year}-Q{q}")
        ids = sorted(pool["entry_id"].tolist())
        chosen = rng.choice(ids)
        row = grp[grp["entry_id"] == chosen].iloc[0]
        picks.append({
            "year": year, "quarter": q, "entry_id": chosen, "name": row["name"],
            "name_date": row["name_date"].date().isoformat(), "is_edoc": row["is_edoc"],
            "page_count": row["page_count"], "in_gold": row["in_gold"],
            "meetings_in_quarter": len(grp), "seed": seed,
        })
    df = pd.DataFrame(picks)
    df.to_csv(SAMPLE_CSV, index=False)
    print(f"Sample: {len(df)} meetings across {df['year'].nunique()} years "
          f"({int(df['in_gold'].sum())} in the hand-transcribed set); "
          f"{int(df['page_count'].fillna(0).sum())} pages.")
    return df
