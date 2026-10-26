# Extraction accuracy (quarterly sample)

Reference: the 41 hand-transcribed meetings (2021-05 → 2022-12) in `minutes.json`. The reference is volunteer-typed and has its own errors; read disagreements before counting them against the extractor.

## Summary against the reference

| mode     |   meetings_scored |   date_match |   attendance_exact |   attendance_recall |   consent_yeas_exact |   consent_nays_exact |   hearing_count_match |   hearing_mover_match |   hearing_yeas_match |   hearing_nays_match |   open_comment_recall |
|:---------|------------------:|-------------:|-------------------:|--------------------:|---------------------:|---------------------:|----------------------:|----------------------:|---------------------:|---------------------:|----------------------:|
| balanced |                41 |         0.90 |               0.85 |                1.00 |                 0.68 |                 0.90 |                  0.46 |                  0.50 |                 0.57 |                 0.96 |                  0.68 |
| fast     |                41 |         0.90 |               0.83 |                1.00 |                 0.63 |                 0.90 |                  0.37 |                  0.55 |                 0.72 |                 0.96 |                  0.68 |

## Balanced vs. fast on every sampled meeting, by 5-year era

No reference exists before 2021, so agreement between the two modes is the signal there. Fewer motions in one mode almost always means it missed some.

| era   |   meetings |   attendance_agree |   motions_balanced |   motions_fast |   recorded_votes_balanced |   recorded_votes_fast |
|:------|-----------:|-------------------:|-------------------:|---------------:|--------------------------:|----------------------:|
| 2000s |         20 |               0.90 |               9.50 |           8.55 |                      8.25 |                  8.50 |
| 2005s |         14 |               0.93 |              11.64 |           9.00 |                     10.71 |                  8.79 |
| 2010s |         20 |               0.95 |               7.65 |           8.60 |                      6.15 |                  7.15 |
| 2015s |          3 |               1.00 |               3.00 |           2.33 |                      1.67 |                  2.00 |
| 2020s |         41 |               0.98 |               5.39 |           4.68 |                      4.44 |                  4.24 |

## Disagreements checked against the minutes

Each row was read in the OCR'd minutes by hand (`data/lookups/adjudications.csv`). `reference_error` means the extraction matches the minutes and the hand transcription does not.

| field        | verdict         |   n |
|:-------------|:----------------|----:|
| attendance   | reference_error |   6 |
| attendance   | scorer_fixed    |   1 |
| consent_vote | both_partial    |   1 |
| consent_vote | pipeline_fixed  |   1 |
| hearing_vote | reference_error |   1 |
| meeting_date | reference_error |   4 |

|   entry_id | field        | reference_says                               | extraction_says                                                                                    | minutes_say                                                                                                                                                   | verdict         |
|-----------:|:-------------|:---------------------------------------------|:---------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------|
|     177597 | meeting_date | 2022-09-14                                   | 2021-09-14                                                                                         | Roll call lists the 2021 council (Swetlick, Weaver, Young)                                                                                                    | reference_error |
|     178691 | meeting_date | 2022-02-15                                   | 2022-01-04                                                                                         | Heading: Tuesday, January 4, 2022                                                                                                                             | reference_error |
|     179520 | meeting_date | 2022-01-01                                   | 2022-03-01                                                                                         | Heading: Tuesday, March 1, 2022                                                                                                                               | reference_error |
|     177182 | attendance   | omits Weaver                                 | includes Weaver                                                                                    | Mayor Weaver called the meeting to order; the members-present line lists council members only                                                                 | reference_error |
|     177183 | attendance   | omits Weaver                                 | includes Weaver                                                                                    | Mayor Weaver called the meeting to order at 6:01 p.m.                                                                                                         | reference_error |
|     177185 | attendance   | omits Weaver                                 | includes Weaver                                                                                    | Mayor presides; members-present line omits the mayor                                                                                                          | reference_error |
|     177180 | attendance   | omits Weaver                                 | includes Weaver                                                                                    | Mayor presides; members-present line omits the mayor                                                                                                          | reference_error |
|     178246 | attendance   | omits Joseph                                 | includes Joseph                                                                                    | Council Members present virtually: Brockett, Friend, Joseph, Nagle, …                                                                                         | reference_error |
|     181341 | attendance   | omits Folkerts, Friend                       | includes Folkerts, Friend                                                                          | Virtually present: Folkerts, Friend                                                                                                                           | reference_error |
|     179600 | attendance   | lists "Yates - Late"                         | includes Yates                                                                                     | Yates arrived late; present                                                                                                                                   | scorer_fixed    |
|     178246 | consent_vote | 9 yeas                                       | 9 yeas; Nagle: no on item F (item_level_exceptions)                                                | Carried 9:0 — NAY: Nagle on Item F – carried 8:1                                                                                                              | both_partial    |
|     179600 | consent_vote | 8 yeas                                       | 8 yeas; Yates left out (inferred_from_attendance_note: "arrived at 8:06 p.m.")                     | Carried 8:0 — Yates had not yet arrived                                                                                                                       | pipeline_fixed  |
|     179146 | meeting_date | 2022-02-02                                   | 2022-02-01                                                                                         | Heading: Tuesday, February 1, 2022 (document name says 02.02.2022)                                                                                            | reference_error |
|     177180 | hearing_vote | yeas include Nagle, omit Brockett and Weaver | 8 yeas: all present but Nagle (fast: inferred_from_attendance_note; balanced: Nagle stated absent) | NOTE: Mayor Weaver announced that Council Member Nagle has left the meeting at 8:20 p.m.; Ordinances 8466 and 8462 moved/seconded with Brockett, Carried: 8:0 | reference_error |

## Disagreements to adjudicate — balanced

- `177597` date: ref=2022-09-14 | ext=2021-09-14
- `179599` 2022-03-15 hearing “ordinance 8500”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `178243` 2021-09-21 hearing “adopt resolution 1295”: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle'] | ext yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Nagle']
- `178243` 2021-09-21 hearing “adopt resolution 1295”: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle'] | ext yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Nagle']
- `177182` 2021-07-13: reference hearing not found: “concept plan review”
- `177182` 2021-07-13 attendance: ref=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177182` 2021-07-13 consent vote: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `178691` date: ref=2022-02-15 | ext=2022-01-04
- `178691` 2022-02-15: reference hearing not found: “description:”
- `178691` 2022-02-15 consent vote: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `179520` date: ref=2022-01-01 | ext=2022-03-01
- `179520` 2022-01-01 hearing “update on state legislation and consideration of revisions”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `179931` 2022-05-24: reference hearing not found: “description:”
- `180021` 2022-06-14 hearing “ordinance 8521”: ref yeas=['Friend', 'Wallach', 'Winer', 'Yates'] nays=['Benjamin', 'Brockett', 'Folkerts', 'Joseph', 'Speer'] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `180021` 2022-06-14 consent vote: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `178246` 2021-10-05: reference hearing not found: “description:”
- `178246` 2021-10-05 attendance: ref=['Brockett', 'Friend', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young']
- `178246` 2021-10-05 consent vote: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `178365` 2021-10-19: reference hearing not found: “lynn segal”
- `178614` 2021-11-16 hearing “motion to adopt ordinance 8490”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `178614` 2021-11-16 hearing “motion to adopt ordinance 8513”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `176772` 2021-05-04: reference hearing not found: “consideration of a nonconforming use review”
- `181346` 2022-08-18 hearing “ordinance 8534”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `181346` 2022-08-18 hearing “ordinance 8546”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer'] nays=['Wallach', 'Winer', 'Yates'] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `181346` 2022-08-18 hearing “ordinance 8546”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer'] nays=['Wallach', 'Winer', 'Yates'] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `181344` 2022-10-13 hearing “2023 policy statement”: ref yeas=[] nays=[] | ext yeas=['Benjamin', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `181344` 2022-10-13 consent vote: ref yeas=['Benjamin', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `178613` 2021-11-09 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Absent', 'Nagle'] | ext yeas=[] nays=[]
- `177187` 2021-08-17 hearing “ordinance 8474”: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[] | ext yeas=[] nays=[]
- `177187` 2021-08-17 hearing “ordinance 8475”: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[] | ext yeas=[] nays=[]
- `177187` 2021-08-17 hearing “ordinance 8480”: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[] | ext yeas=[] nays=[]
- `177183` 2021-07-20 hearing “ordinance 8470”: ref yeas=['Brockett', 'Nagle', 'Wallach', 'Yates', 'Young'] nays=['Friend', 'Joseph', 'Swetlick'] | ext yeas=['Brockett', 'Nagle', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Friend', 'Joseph', 'Swetlick']
- `177183` 2021-07-20 attendance: ref=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177183` 2021-07-20 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 hearing “ordinance 8476”: ref yeas=['Amended'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 hearing “ordinance 8486”: ref yeas=['Amended'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 hearing “ordinance 8477”: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 attendance: ref=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177185` 2021-08-03 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=[]
- `177596` 2021-09-09 consent vote: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Joseph', 'Yates'] | ext yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=[]
- `177180` 2021-06-15 hearing “second reading and consideration of a motion to adopt ordina”: ref yeas=['Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177180` 2021-06-15 hearing “second reading and consideration of a motion to adopt ordina”: ref yeas=[] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177180` 2021-06-15 hearing “second reading and consideration of a motion to adopt ordina”: ref yeas=['Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177180` 2021-06-15 attendance: ref=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177180` 2021-06-15 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177186` 2021-08-10 consent vote: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Nagle'] | ext yeas=[] nays=[]
- `181148` 2022-10-06 hearing “items relating to the east boulder subcommunity plan”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `181343` 2022-12-01: reference hearing not found: “drcog”
- `176815` 2021-05-18: reference hearing not found: “julia hanke, gina mcafee, nicole speer, joni teter, bruce norikane, nicole perelman, joann”
- `176815` 2021-05-18 consent vote: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Yates'] nays=['Brockett', 'F', 'Friend', 'N', 'Nagle', 'Swetlick'] | ext yeas=[] nays=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach']
- `178366` 2021-10-26 hearing “ordinance 8510”: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle'] | ext yeas=['Brockett', 'Friend', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle']
- `181341` 2022-11-03 hearing “resolution 1321”: ref yeas=['Brockett', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=['Joseph'] | ext yeas=['Brockett', 'Folkerts', 'Friend', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=['Joseph']
- `181341` 2022-11-03 attendance: ref=['Brockett', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] | ext=['Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates']
- `181341` 2022-11-03 consent vote: ref yeas=['Brockett', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=['Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `179146` date: ref=2022-02-02 | ext=2022-02-01
- `179146` 2022-02-02 hearing “ordinance 8496”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `179146` 2022-02-02 consent vote: ref yeas=['Wallach', 'Yates'] nays=[] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]

## Disagreements to adjudicate — fast

- `177597` date: ref=2022-09-14 | ext=2021-09-14
- `177597` 2022-09-14 hearing “public hearing and consideration of the following items rela”: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=[] | ext yeas=[] nays=[]
- `181345` 2022-10-20 hearing “ordinance 8535 ordinance 8536 ordinance 8537 ordinance 8538”: ref yeas=['Benjamin', 'Friend', 'Joseph', 'Wallach', 'Winer', 'Yates'] nays=['Folkerts', 'Speer'] | ext yeas=['Benjamin', 'Friend', 'Joseph', 'Winer', 'Yates'] nays=['Folkerts', 'Speer']
- `178243` 2021-09-21 hearing “adopt resolution 1295”: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle'] | ext yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Nagle']
- `178243` 2021-09-21 hearing “adopt resolution 1295”: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle'] | ext yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Nagle']
- `177182` 2021-07-13: reference hearing not found: “concept plan review”
- `177182` 2021-07-13 attendance: ref=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177182` 2021-07-13 consent vote: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `178691` date: ref=2022-02-15 | ext=2022-01-04
- `178691` 2022-02-15: reference hearing not found: “description:”
- `178691` 2022-02-15 consent vote: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `179520` date: ref=2022-01-01 | ext=2022-03-01
- `179520` 2022-01-01 hearing “update on state legislation and consideration of revisions”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `179931` 2022-05-24: reference hearing not found: “description:”
- `180021` 2022-06-14 hearing “ordinance 8521”: ref yeas=['Friend', 'Wallach', 'Winer', 'Yates'] nays=['Benjamin', 'Brockett', 'Folkerts', 'Joseph', 'Speer'] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `180021` 2022-06-14 consent vote: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `178246` 2021-10-05: reference hearing not found: “description:”
- `178246` 2021-10-05 attendance: ref=['Brockett', 'Friend', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young']
- `178246` 2021-10-05 consent vote: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `178365` 2021-10-19: reference hearing not found: “lynn segal”
- `176772` 2021-05-04: reference hearing not found: “consideration of a nonconforming use review”
- `176772` 2021-05-04 attendance: ref=['Brockett', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `181346` 2022-08-18 hearing “ordinance 8534”: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer'] nays=['Wallach', 'Winer', 'Yates']
- `181346` 2022-08-18: reference hearing not found: “ordinance 8539”
- `181346` 2022-08-18: reference hearing not found: “ordinance 8540”
- `181346` 2022-08-18: reference hearing not found: “ordinance 8542”
- `181344` 2022-10-13 consent vote: ref yeas=['Benjamin', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `178613` 2021-11-09 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Absent', 'Nagle'] | ext yeas=[] nays=[]
- `177183` 2021-07-20 hearing “ordinance 8470”: ref yeas=['Brockett', 'Nagle', 'Wallach', 'Yates', 'Young'] nays=['Friend', 'Joseph', 'Swetlick'] | ext yeas=['Brockett', 'Nagle', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Friend', 'Joseph', 'Swetlick']
- `177183` 2021-07-20 attendance: ref=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177183` 2021-07-20 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `181147` 2022-09-15: reference hearing not found: “comprehensive flood and stormwater master plan”
- `177185` 2021-08-03 hearing “ordinance 8476”: ref yeas=['Amended'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 hearing “ordinance 8486”: ref yeas=['Amended'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 hearing “ordinance 8477”: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177185` 2021-08-03 attendance: ref=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177185` 2021-08-03 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=[]
- `177596` 2021-09-09 consent vote: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Joseph', 'Yates'] | ext yeas=[] nays=[]
- `177180` 2021-06-15 hearing “second reading and consideration of a motion to adopt ordina”: ref yeas=['Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177180` 2021-06-15 hearing “second reading and consideration of a motion to adopt ordina”: ref yeas=['Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177180` 2021-06-15 attendance: ref=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] | ext=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young']
- `177180` 2021-06-15 consent vote: ref yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Yates', 'Young'] nays=[] | ext yeas=['Brockett', 'Friend', 'Joseph', 'Nagle', 'Swetlick', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=[]
- `177186` 2021-08-10 consent vote: ref yeas=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young'] nays=['Nagle'] | ext yeas=['Nagle'] nays=['Brockett', 'Friend', 'Swetlick', 'Wallach', 'Weaver', 'Young']
- `181148` 2022-10-06: reference hearing not found: “items relating to the 2023 budget”
- `181343` 2022-12-01: reference hearing not found: “drcog”
- `181343` 2022-12-01: reference hearing not found: “mayor pro term election”
- `176815` 2021-05-18: reference hearing not found: “julia hanke, gina mcafee, nicole speer, joni teter, bruce norikane, nicole perelman, joann”
- `176815` 2021-05-18 consent vote: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlick', 'Wallach', 'Yates'] nays=['Brockett', 'F', 'Friend', 'N', 'Nagle', 'Swetlick'] | ext yeas=[] nays=[]
- `178366` 2021-10-26 hearing “ordinance 8510”: ref yeas=['Brockett', 'Friend', 'Nagle', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle'] | ext yeas=['Brockett', 'Friend', 'Swetlik', 'Wallach', 'Weaver', 'Yates', 'Young'] nays=['Nagle']
- `178615` 2021-11-30 consent vote: ref yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=[] nays=[]
- `181341` 2022-11-03 hearing “resolution 1321”: ref yeas=['Brockett', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=['Joseph'] | ext yeas=['Brockett', 'Folkerts', 'Friend', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=['Joseph']
- `181341` 2022-11-03 attendance: ref=['Brockett', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] | ext=['Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates']
- `181341` 2022-11-03 consent vote: ref yeas=['Brockett', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[] | ext yeas=['Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]
- `179146` date: ref=2022-02-02 | ext=2022-02-01
- `179146` 2022-02-02 consent vote: ref yeas=['Wallach', 'Yates'] nays=[] | ext yeas=['Benjamin', 'Brockett', 'Folkerts', 'Friend', 'Joseph', 'Speer', 'Wallach', 'Winer', 'Yates'] nays=[]

Sample definition: `data/lookups/sample_quarterly.csv`.
