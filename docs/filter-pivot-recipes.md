# Filter and pivot recipes

The tables are long (one row per member × motion, etc.). These recipes recover the
wide views people usually want.

## How often did each member vote no, by year?

**pandas**

```python
import pandas as pd

votes = pd.read_csv("data/processed/member_votes.csv")
meetings = pd.read_csv("data/processed/meetings.csv")
v = votes.merge(meetings[["entry_id", "meeting_date"]], on="entry_id")
v["year"] = v["meeting_date"].str[:4]
(v[v["vote"].isin(["yes", "no"])]
   .assign(no=lambda d: d["vote"].eq("no"))
   .pivot_table(index="member", columns="year", values="no", aggfunc="mean"))
```

**R / tidyverse**

```r
library(tidyverse)
votes <- read_csv("data/processed/member_votes.csv")
meetings <- read_csv("data/processed/meetings.csv")
votes |>
  inner_join(meetings |> select(entry_id, meeting_date), by = "entry_id") |>
  filter(vote %in% c("yes", "no")) |>
  mutate(year = substr(meeting_date, 1, 4)) |>
  group_by(member, year) |>
  summarise(no_share = mean(vote == "no"), .groups = "drop") |>
  pivot_wider(names_from = year, values_from = no_share)
```

## Only votes the minutes actually state

Add `votes[votes["vote_source"] == "stated"]` (pandas) or
`filter(vote_source == "stated")` (R). Inferred rows assume every present, unnamed
member voted yes — see `docs/data-dictionary.md`. To keep inferred rows but drop the
ones that relied on late-arrival / early-departure notes, filter
`inference_basis != "attendance_note"`.

## Split votes only (one row per motion, members as columns)

```python
motions = pd.read_csv("data/processed/motions.csv")
split = motions[motions["n_no"] > 0][["entry_id", "motion_seq"]]
(votes.merge(split, on=["entry_id", "motion_seq"])
      .pivot_table(index=["entry_id", "motion_seq"], columns="member",
                   values="vote", aggfunc="first"))
```

```r
motions <- read_csv("data/processed/motions.csv")
votes |>
  semi_join(motions |> filter(n_no > 0), by = c("entry_id", "motion_seq")) |>
  pivot_wider(id_cols = c(entry_id, motion_seq), names_from = member, values_from = vote)
```

## Attendance grid (meeting × member)

```python
att = pd.read_csv("data/processed/attendance.csv")
att.pivot_table(index="meeting_date", columns="member", values="status", aggfunc="first")
```

## Spreadsheet users

Open `member_votes.csv` in Excel or Google Sheets → Insert → PivotTable → Rows: `member`,
Columns: `vote`, Values: COUNTA of `motion_seq`. Add a filter on `vote_source` to
exclude inferred votes.
