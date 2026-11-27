# Report build and evidence map

From this directory, run `make` to regenerate the three figures and build
`main.pdf`. The build uses latexmk when available, otherwise Tectonic.
Install the plotting environment once with `make plot-env` if needed.

| Report item | Source | Reproduction script |
| --- | --- | --- |
| Figure 1, shared-memory evidence | data/test_record.csv; Week 2 logs | ../analysis/plot_shared_memory.py |
| Figure 2, checker outcomes | results/week3_full_suite/run-20261116T150500Z-ixxI8j/summary.tsv | ../analysis/plot_reproduction.py |
| Figure 3, race warnings | Same Week 3 directory: race_warning_counts.tsv; paper Table 12 for left panel | ../analysis/plot_race_detection.py |
| Tables 5 and 7, Week 2 outcomes and records | data/test_record.csv; results/week2_full_suite/ | sections/results.tex; tables/test_record.tex |
| Tables 8 and 9, extension | data/extension_record.csv; ../extension/results/run-20261118T115819Z-IAbvyc/ | tables/extension_record.tex |

Paper figure numbers (1, 5, 8, 10) identify the original bug examples;
report figure numbers (1, 2, 3) identify the generated visualizations.
Cross-references inside the report use LaTeX labels.

Run `python3 analysis/check_report_consistency.py` from the repository root
to check archived records against logs, table values, durations, assets,
and reference keys. This does not rerun Go experiments or independently
revalidate the original paper's benchmark counts.

2026-11-26 review: fixed floating tables in Sections 4.1 and 4.2,
kept headings with their associated content, corrected the Week 2 / Week 3
figure provenance wording, clarified original-paper figure numbers, and
expanded test paths relative to bugs/. Archived experiment data and
references.bib are unchanged. PDF pagination may change after edits.
