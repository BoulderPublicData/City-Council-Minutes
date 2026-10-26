import pandas as pd

from scripts import schema
from scripts.tidy import tidy_one

ENTRY = {"entry_id": 151897, "name": "Minutes - Apr-01-2003", "name_date": "2003-04-01",
         "name_meeting_type": None, "page_count": 6.0,
         "docview_url": "https://documents.bouldercolorado.gov/WebLink/DocView.aspx?id=151897&dbid=0&repo=LF8PROD2"}


def test_tidy_one_2003(extraction_2003):
    t = tidy_one(ENTRY, extraction_2003, "balanced", "test")
    m = t["meetings"][0]
    assert m["meeting_date"] == "2003-04-01"
    assert m["n_members_present"] == 9
    motions = pd.DataFrame(t["motions"])
    split = motions[motions["yes_count"] == 6].iloc[0]
    assert split["vote_inference"] == "inferred_from_roll_call"
    assert (split["n_yes"], split["n_no"]) == (6, 3)
    # the minutes' typo "Poinssatte" is snapped to the roll call spelling
    assert "Poinssatte" not in set(motions["seconded_by"].dropna())


def test_tidy_tables_validate(extraction_2003):
    t = tidy_one(ENTRY, extraction_2003, "balanced", "test")
    for name, sch in schema.TABLES.items():
        df = pd.DataFrame(t[name], columns=list(sch.columns) + (["_call_ups"] if name == "meetings" else []))
        df = df.drop(columns=["_call_ups"], errors="ignore")
        for col, c in sch.columns.items():
            if str(c.dtype) == "Int64":
                df[col] = df[col].astype("Int64")
        sch.validate(df)


def test_nested_export_has_no_nan(extraction_2003):
    import json

    from scripts.tidy import nested_meeting
    t = tidy_one(ENTRY, extraction_2003, "balanced", "test")
    tables = {name: pd.DataFrame(rows) for name, rows in t.items()}
    out = json.dumps(nested_meeting(tables, 151897))
    assert "NaN" not in out
