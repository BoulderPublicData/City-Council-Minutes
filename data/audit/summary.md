# Audit summary

## Inventory (Laserfiche `Signed Minutes`)

771 documents; 0 have no parseable date in their name (listed below). *imaged* = scanned pages, PDF rendered by the portal.

|   year_folder |   documents |   pages |   imaged |   undated_names |
|--------------:|------------:|--------:|---------:|----------------:|
|          2000 |          26 |     196 |       26 |               0 |
|          2001 |          26 |     193 |       26 |               0 |
|          2002 |          26 |     198 |       26 |               0 |
|          2003 |          25 |     184 |       25 |               0 |
|          2004 |          23 |     181 |       23 |               0 |
|          2005 |          31 |     209 |       31 |               0 |
|          2006 |          26 |     216 |       26 |               0 |
|          2007 |          28 |     237 |       28 |               0 |
|          2008 |          25 |     309 |       25 |               0 |
|          2009 |          26 |     231 |       26 |               0 |
|          2010 |          29 |     250 |       29 |               0 |
|          2011 |          29 |     283 |       29 |               0 |
|          2012 |          26 |     237 |       26 |               0 |
|          2013 |          32 |     320 |       14 |               0 |
|          2014 |          25 |     218 |        0 |               0 |
|          2015 |          41 |     193 |        0 |               0 |
|          2016 |          36 |     108 |        0 |               0 |
|          2017 |          37 |     218 |        0 |               0 |
|          2018 |          30 |     218 |        0 |               0 |
|          2019 |          32 |     193 |        0 |               0 |
|          2020 |          34 |     167 |        0 |               0 |
|          2021 |          32 |     161 |        0 |               0 |
|          2022 |          30 |     193 |        0 |               0 |
|          2023 |          29 |     173 |        0 |               0 |
|          2024 |          28 |     151 |        0 |               0 |
|          2025 |          26 |     143 |        0 |               0 |
|          2026 |          13 |      73 |        0 |               0 |

### Documents whose name doesn't say “minutes”

Kept in the inventory; check whether any are not council minutes.

|   entry_id | name                           | folder_path                                              |
|-----------:|:-------------------------------|:---------------------------------------------------------|
|     130803 | City Council Minues - 10.20.15 | \Central Records\City Council\Signed Minutes\2015\10 OCT |

## Downloads

140 PDFs on disk (29 rendered from page images). 4 have a page count different from the portal's.

|   entry_id | name                                               |   pdf_pages |   inventory_pages |
|-----------:|:---------------------------------------------------|------------:|------------------:|
|     131169 | City Council Minutes - 11-10.2015                  |           8 |                 0 |
|     131726 | City Council Minutes - 01-26-2016  Special Meeting |           1 |                 0 |
|     134709 | City Council Minutes - 2016-05-16                  |           2 |                 0 |
|     137435 | City Council Minutes - 2016-08-02                  |           8 |                 0 |

## Extracted meetings by era

`present_lt_5` counts meetings where fewer than five members were found present — almost always a missed roll call, since council needs five for a quorum. More than nine present happens at post-election transition meetings.

| era   |   meetings |   present_mean |   present_lt_5 |   motions_mean |   items_mean |   date_disagrees |
|:------|-----------:|---------------:|---------------:|---------------:|-------------:|-----------------:|
| 2000s |         20 |           7.95 |              0 |           9.50 |        27.15 |                0 |
| 2005s |         14 |           8.29 |              0 |          11.64 |        31.07 |                0 |
| 2010s |         20 |           8.70 |              0 |           7.65 |        28.30 |                1 |
| 2015s |          3 |           8.67 |              0 |           3.00 |        13.00 |                0 |
| 2020s |         41 |           8.54 |              0 |           5.39 |        23.29 |                1 |

### How each motion's per-member votes were obtained (share of motions)

| era   |   inconsistent_not_inferred |   inferred_from_attendance_note |   inferred_from_roll_call |   inferred_with_item_exceptions |   no_vote_recorded |   partial_stated_only |
|:------|----------------------------:|--------------------------------:|--------------------------:|--------------------------------:|-------------------:|----------------------:|
| 2000s |                        0.12 |                            0.00 |                      0.73 |                            0.01 |               0.13 |                  0.01 |
| 2005s |                        0.07 |                            0.00 |                      0.80 |                            0.01 |               0.08 |                  0.04 |
| 2010s |                        0.12 |                            0.00 |                      0.65 |                            0.02 |               0.20 |                  0.02 |
| 2015s |                        0.00 |                            0.00 |                      0.56 |                            0.00 |               0.44 |                  0.00 |
| 2020s |                        0.03 |                            0.01 |                      0.73 |                            0.03 |               0.18 |                  0.02 |

### Missing motion fields (share of motions)

| era   |   motions |   moved_by_missing |   seconded_missing |   vote_text_missing |
|:------|----------:|-------------------:|-------------------:|--------------------:|
| 2000s |       190 |               0.17 |               0.19 |                0.13 |
| 2005s |       163 |               0.19 |               0.28 |                0.07 |
| 2010s |       153 |               0.15 |               0.22 |                0.20 |
| 2015s |         9 |               0.33 |               0.33 |                0.44 |
| 2020s |       221 |               0.24 |               0.29 |                0.21 |

### Meetings to check by hand

|   entry_id | meeting_date   | document_name                     |   n_members_present | date_disagrees_with_name   |
|-----------:|:---------------|:----------------------------------|--------------------:|:---------------------------|
|     126340 | 2014-08-01     | City Council Minutes - 2014-08-05 |                   9 | True                       |
|     152022 | 2001-11-13     | Minutes - Nov-13-2001             |                  10 | False                      |
|     179146 | 2022-02-01     | City Council Minutes - 02.02.2022 |                   9 | True                       |

## Names dropped from the roll call

9 names the extractor listed as council members were dropped by `tidy.non_members` (public speakers who didn't show, other boards' members). Check that none is a real council member.

|   entry_id | meeting_date   | name_as_printed   | status   | note         | reason                                                                        |
|-----------:|:---------------|:------------------|:---------|:-------------|:------------------------------------------------------------------------------|
|      11796 | 2008-07-08     | W. JOHNSON        | absent   | ABSENT       | no council title, no action in the meeting, not on a roll call within 3 years |
|      11796 | 2008-07-08     | E. JONES          | absent   | ABSENT       | no council title, no action in the meeting, not on a roll call within 3 years |
|     177185 | 2021-08-03     | Michael Parrish   | absent   | NOT PRESENT  | no council title, no action in the meeting, not on a roll call within 3 years |
|     179600 | 2022-04-05     | Fred Bratman      | absent   | DID NOT SHOW | no council title, no action in the meeting, not on a roll call within 3 years |
|     179600 | 2022-04-05     | Cate Lawrence     | absent   | WITHDREW     | no council title, no action in the meeting, not on a roll call within 3 years |
|     179600 | 2022-04-05     | John Walker       | absent   | DID NOT SHOW | no council title, no action in the meeting, not on a roll call within 3 years |
|     179600 | 2022-04-05     | Kate Weiner       | absent   | DID NOT SHOW | no council title, no action in the meeting, not on a roll call within 3 years |
|     181343 | 2022-12-01     | Christy Gunter    | absent   | not present  | no council title, no action in the meeting, not on a roll call within 3 years |
|     181343 | 2022-12-01     | Kent Welley       | absent   | not present  | no council title, no action in the meeting, not on a roll call within 3 years |

## Datalab cost and full-run projection

Spent so far (all runs, including retries and tests): **$30.42**.
Full archive: **771 documents, ~5,453 pages** (page counts from the portal listing; missing counts filled with the median).

- convert + **balanced** extraction, whole archive: **≈ $183**
- convert + **fast** extraction, whole archive: **≈ $42**

| step    | mode     |   docs |   pages |   cost_usd |   usd_per_1k_pages |   projected_full_archive_usd |
|:--------|:---------|-------:|--------:|-----------:|-------------------:|-----------------------------:|
| convert | balanced |    140 | 1023.00 |       3.01 |               2.94 |                        16.06 |
| extract | balanced |     98 |  735.00 |      22.46 |              30.56 |                       166.66 |
| extract | fast     |    140 | 1023.00 |       4.95 |               4.83 |                        26.36 |

Sample: 106 meetings, 811 pages, 7 with a hand-transcribed reference.

